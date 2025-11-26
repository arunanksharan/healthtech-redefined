"use client";

import * as React from "react";
import { useState, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Inbox,
  Calendar,
  Users,
  UserCog,
  Building2,
  MapPin,
  CalendarDays,
  Clock,
  ClipboardList,
  Hospital,
  Microscope,
  Stethoscope,
  Pill,
  FlaskConical,
  BarChart3,
  MessageSquare,
  Video,
  CreditCard,
  Settings,
  ChevronDown,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  LogOut,
  Moon,
  Sun,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useTheme } from "@/components/providers/theme-provider";
import { Badge } from "@/components/ui/badge";

// Navigation configuration
interface NavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  badge?: string;
}

interface NavSection {
  id: string;
  title: string;
  collapsible?: boolean;
  items: NavItem[];
}

const navigationConfig: NavSection[] = [
  {
    id: "main",
    title: "Main",
    items: [
      { id: "dashboard", label: "Dashboard", icon: Home, href: "/" },
      { id: "inbox", label: "Inbox", icon: Inbox, href: "/inbox", badge: "unreadCount" },
      { id: "schedule", label: "Schedule", icon: Calendar, href: "/schedule" },
    ],
  },
  {
    id: "fhir-entities",
    title: "FHIR Entities",
    collapsible: true,
    items: [
      { id: "patients", label: "Patients", icon: Users, href: "/patients" },
      { id: "practitioners", label: "Practitioners", icon: UserCog, href: "/practitioners" },
      { id: "organizations", label: "Organizations", icon: Building2, href: "/organizations" },
      { id: "locations", label: "Locations", icon: MapPin, href: "/locations" },
      { id: "schedules", label: "Schedules", icon: CalendarDays, href: "/schedules" },
      { id: "slots", label: "Slots", icon: Clock, href: "/slots" },
      { id: "appointments", label: "Appointments", icon: ClipboardList, href: "/appointments" },
      { id: "encounters", label: "Encounters", icon: Hospital, href: "/encounters" },
      { id: "observations", label: "Observations", icon: Microscope, href: "/observations" },
      { id: "conditions", label: "Conditions", icon: Stethoscope, href: "/conditions" },
      { id: "medications", label: "Medications", icon: Pill, href: "/medications" },
      { id: "diagnostic-reports", label: "DiagnosticReports", icon: FlaskConical, href: "/diagnostic-reports" },
    ],
  },
  {
    id: "workflows",
    title: "Workflows",
    items: [
      { id: "analytics", label: "Analytics", icon: BarChart3, href: "/analytics" },
      { id: "collaboration", label: "Collaboration", icon: MessageSquare, href: "/collaboration" },
      { id: "telehealth", label: "Telehealth", icon: Video, href: "/telehealth" },
      { id: "billing", label: "Billing", icon: CreditCard, href: "/billing" },
    ],
  },
];

// Badge counts - would come from API in real app
const useBadgeCounts = () => {
  return {
    unreadCount: 12,
  };
};

interface SidebarProps {
  className?: string;
  onCollapsedChange?: (collapsed: boolean) => void;
}

export function Sidebar({ className, onCollapsedChange }: SidebarProps) {
  const pathname = usePathname();
  const { theme, setTheme, resolvedTheme } = useTheme();
  const badges = useBadgeCounts();

  const [collapsed, setCollapsed] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());

  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      const newValue = !prev;
      onCollapsedChange?.(newValue);
      return newValue;
    });
  }, [onCollapsedChange]);

  const toggleSection = useCallback((sectionId: string) => {
    setCollapsedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  }, []);

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/" || pathname === "/dashboard";
    }
    return pathname.startsWith(href);
  };

  return (
    <aside
      className={cn(
        "h-full bg-card border-r border-border flex flex-col transition-all duration-200 ease-in-out",
        collapsed ? "w-sidebar-collapsed" : "w-sidebar",
        className
      )}
    >
      {/* Logo */}
      <div className="h-topbar flex items-center justify-between px-4 border-b border-border">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Hospital className="w-5 h-5 text-primary-foreground" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-foreground">HealthPRM</span>
              <span className="text-xs text-muted-foreground">Surya Hospitals</span>
            </div>
          )}
        </Link>
        <button
          onClick={toggleCollapsed}
          className="p-1.5 rounded-md hover:bg-accent transition-colors"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronsRight className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronsLeft className="w-4 h-4 text-muted-foreground" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2">
        {navigationConfig.map((section) => (
          <div key={section.id} className="mb-4">
            {/* Section Header */}
            {!collapsed && (
              <div className="px-3 mb-2">
                {section.collapsible ? (
                  <button
                    onClick={() => toggleSection(section.id)}
                    className="flex items-center justify-between w-full text-xs font-semibold text-muted-foreground uppercase tracking-wider hover:text-foreground transition-colors"
                  >
                    <span>{section.title}</span>
                    {collapsedSections.has(section.id) ? (
                      <ChevronRight className="w-3 h-3" />
                    ) : (
                      <ChevronDown className="w-3 h-3" />
                    )}
                  </button>
                ) : (
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {section.title}
                  </span>
                )}
              </div>
            )}

            {/* Section Items */}
            {(!section.collapsible || !collapsedSections.has(section.id)) && (
              <div className="space-y-1">
                {section.items.map((item) => {
                  const active = isActive(item.href);
                  const badgeValue = item.badge ? badges[item.badge as keyof typeof badges] : undefined;

                  return (
                    <Link
                      key={item.id}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors relative group",
                        "hover:bg-accent hover:text-accent-foreground",
                        active && "bg-primary/10 text-primary border-l-2 border-primary -ml-0.5 pl-[calc(0.75rem+2px)]",
                        !active && "text-muted-foreground",
                        collapsed && "justify-center px-2"
                      )}
                      title={collapsed ? item.label : undefined}
                    >
                      <item.icon className={cn("w-5 h-5 shrink-0", active && "text-primary")} />

                      {!collapsed && (
                        <>
                          <span className="flex-1 truncate">{item.label}</span>
                          {badgeValue !== undefined && badgeValue > 0 && (
                            <Badge variant="secondary" className="ml-auto text-xs h-5 min-w-5 flex items-center justify-center">
                              {badgeValue > 99 ? "99+" : badgeValue}
                            </Badge>
                          )}
                        </>
                      )}

                      {/* Tooltip for collapsed state */}
                      {collapsed && (
                        <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-sm rounded-md shadow-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap z-50 border border-border">
                          {item.label}
                          {badgeValue !== undefined && badgeValue > 0 && (
                            <Badge variant="secondary" className="ml-2 text-xs">
                              {badgeValue}
                            </Badge>
                          )}
                        </div>
                      )}

                      {/* Badge indicator for collapsed state */}
                      {collapsed && badgeValue !== undefined && badgeValue > 0 && (
                        <span className="absolute top-1 right-1 w-2 h-2 bg-primary rounded-full" />
                      )}
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* User Profile & Settings */}
      <div className="border-t border-border p-2">
        {/* Theme Toggle */}
        <button
          onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
          className={cn(
            "flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm font-medium transition-colors",
            "hover:bg-accent text-muted-foreground",
            collapsed && "justify-center px-2"
          )}
        >
          {resolvedTheme === "dark" ? (
            <Sun className="w-5 h-5" />
          ) : (
            <Moon className="w-5 h-5" />
          )}
          {!collapsed && <span>Toggle Theme</span>}
        </button>

        {/* Settings Link */}
        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm font-medium transition-colors",
            "hover:bg-accent text-muted-foreground",
            pathname === "/settings" && "bg-primary/10 text-primary",
            collapsed && "justify-center px-2"
          )}
        >
          <Settings className="w-5 h-5" />
          {!collapsed && <span>Settings</span>}
        </Link>

        {/* User Profile */}
        <div
          className={cn(
            "flex items-center gap-3 px-3 py-2 mt-2 rounded-md bg-accent/50",
            collapsed && "justify-center px-2"
          )}
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-primary-foreground text-sm font-semibold">
            RS
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">Dr. Rohit Sharma</p>
              <p className="text-xs text-muted-foreground truncate">Cardiologist</p>
            </div>
          )}
          {!collapsed && (
            <button className="p-1 rounded-md hover:bg-accent transition-colors">
              <LogOut className="w-4 h-4 text-muted-foreground" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
