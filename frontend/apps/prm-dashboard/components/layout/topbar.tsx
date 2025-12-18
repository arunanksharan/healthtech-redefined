"use client";

import * as React from "react";
import { useState, useEffect } from "react";
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

// Mock notification count
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

  useEffect(() => {
    setIsMac(navigator.platform.toUpperCase().indexOf("MAC") >= 0);
  }, []);

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
        "h-topbar bg-white dark:bg-gray-900 border-b-2 border-gray-100 dark:border-gray-800 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-30",
        className
      )}
    >
      {/* Left Section - Menu button and Breadcrumbs */}
      <div className="flex items-center gap-4">
        {showMenuButton && (
          <button
            onClick={onMenuClick}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 hover:scale-105"
            aria-label="Toggle sidebar"
          >
            <Menu className="w-5 h-5 text-gray-500" />
          </button>
        )}

        {/* Breadcrumbs */}
        <nav aria-label="Breadcrumb" className="flex items-center">
          <ol className="flex items-center gap-1.5">
            {breadcrumbs.map((crumb, index) => (
              <li key={index} className="flex items-center">
                {index > 0 && (
                  <ChevronRight className="w-4 h-4 text-gray-300 mx-1.5" />
                )}
                {crumb.href ? (
                  <Link
                    href={crumb.href}
                    className="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors font-medium"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-sm font-semibold text-gray-900 dark:text-white bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded-lg">
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
          className="flex items-center gap-3 w-full px-4 py-2.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 border-2 border-transparent hover:border-gray-200 dark:hover:border-gray-700 rounded-lg text-sm text-gray-500 transition-all duration-200 group focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <Search className="w-4 h-4 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors" />
          <span className="flex-1 text-left">Search or ask AI...</span>
          <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-md text-[10px] font-bold text-gray-400 font-mono">
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
          className="md:hidden p-2.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 text-gray-500 hover:scale-105"
          aria-label="Search"
        >
          <Search className="w-5 h-5" />
        </button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="relative p-2.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 text-gray-500 hover:text-gray-900 dark:hover:text-white hover:scale-105"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-red-500 rounded-full"></span>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80 rounded-lg border-2 border-gray-100 dark:border-gray-800">
            <DropdownMenuLabel className="flex items-center justify-between">
              <span className="font-heading">Notifications</span>
              <span className="bg-blue-500 text-white text-xs font-semibold px-2 py-0.5 rounded-md">{unreadCount} new</span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-gray-100 dark:bg-gray-800" />
            <div className="max-h-80 overflow-y-auto">
              <DropdownMenuItem className="flex flex-col items-start gap-1 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-blue-500 rounded-full" />
                  <span className="font-medium text-sm">New appointment booked</span>
                </div>
                <span className="text-xs text-gray-500 ml-4">
                  Patient John Doe scheduled for tomorrow at 10:00 AM
                </span>
                <span className="text-xs text-gray-400 ml-4">5 min ago</span>
              </DropdownMenuItem>
              <DropdownMenuItem className="flex flex-col items-start gap-1 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-amber-500 rounded-full" />
                  <span className="font-medium text-sm">Lab results available</span>
                </div>
                <span className="text-xs text-gray-500 ml-4">
                  Complete blood count results for Jane Smith
                </span>
                <span className="text-xs text-gray-400 ml-4">1 hour ago</span>
              </DropdownMenuItem>
            </div>
            <DropdownMenuSeparator className="bg-gray-100 dark:bg-gray-800" />
            <DropdownMenuItem className="text-center justify-center text-blue-500 font-semibold cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20">
              View all notifications
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Help */}
        <button
          className="hidden sm:block p-2.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 text-gray-500 hover:text-gray-900 dark:hover:text-white hover:scale-105"
          aria-label="Help"
        >
          <HelpCircle className="w-5 h-5" />
        </button>

        <div className="h-6 w-0.5 bg-gray-200 dark:bg-gray-700 mx-2 hidden sm:block"></div>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 group"
              aria-label="User menu"
            >
              <div className="w-9 h-9 rounded-lg bg-blue-500 flex items-center justify-center text-white text-sm font-bold transition-all duration-200 group-hover:scale-105">
                RS
              </div>
              <ChevronRight className="w-4 h-4 text-gray-400 group-hover:rotate-90 transition-transform duration-200" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60 rounded-lg border-2 border-gray-100 dark:border-gray-800">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-1">
                <span className="font-heading">Dr. Rohit Sharma</span>
                <span className="text-xs font-normal text-gray-500">
                  rohit.sharma@suryahospitals.com
                </span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-gray-100 dark:bg-gray-800" />
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
            <DropdownMenuSeparator className="bg-gray-100 dark:bg-gray-800" />
            <DropdownMenuItem className="flex items-center gap-2 text-red-500 focus:text-red-600 focus:bg-red-50 dark:focus:bg-red-900/20 cursor-pointer">
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
