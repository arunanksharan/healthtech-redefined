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
  Route,
  Ticket,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
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
      { id: "dashboard", label: "Dashboard", icon: Home, href: "/dashboard" },
      { id: "inbox", label: "Inbox", icon: Inbox, href: "/dashboard/inbox", badge: "unreadCount" },
      { id: "schedule", label: "Schedule", icon: Calendar, href: "/dashboard/appointments" },
    ],
  },
  {
    id: "fhir-entities",
    title: "FHIR Entities",
    collapsible: true,
    items: [
      { id: "patients", label: "Patients", icon: Users, href: "/dashboard/patients" },
      { id: "practitioners", label: "Practitioners", icon: UserCog, href: "/dashboard/practitioners" },
      { id: "organizations", label: "Organizations", icon: Building2, href: "/dashboard/organizations" },
      { id: "locations", label: "Locations", icon: MapPin, href: "/dashboard/locations" },
      { id: "schedules", label: "Schedules", icon: CalendarDays, href: "/dashboard/schedules" },
      { id: "slots", label: "Slots", icon: Clock, href: "/dashboard/slots" },

      { id: "encounters", label: "Encounters", icon: Hospital, href: "/dashboard/encounters" },
      { id: "observations", label: "Observations", icon: Microscope, href: "/dashboard/observations" },
      { id: "conditions", label: "Conditions", icon: Stethoscope, href: "/dashboard/conditions" },
      { id: "medications", label: "Medications", icon: Pill, href: "/dashboard/medications" },
      { id: "diagnostic-reports", label: "DiagnosticReports", icon: FlaskConical, href: "/dashboard/diagnostic-reports" },
    ],
  },
  {
    id: "workflows",
    title: "Workflows",
    items: [
      { id: "analytics", label: "Analytics", icon: BarChart3, href: "/dashboard/analytics" },
      { id: "journeys", label: "Care Journeys", icon: Route, href: "/dashboard/journeys" },
      { id: "tickets", label: "Support Tickets", icon: Ticket, href: "/dashboard/tickets" },
      { id: "collaboration", label: "Collaboration", icon: MessageSquare, href: "/dashboard/communications" },
      { id: "telehealth", label: "Telehealth", icon: Video, href: "/dashboard/telehealth" },
      { id: "billing", label: "Billing", icon: CreditCard, href: "/dashboard/billing" },
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
    // Exact match for root or dashboard home
    if (href === "/" || href === "/dashboard") {
      return pathname === href;
    }
    // Partial match for sub-routes (e.g. /dashboard/appointments matches /dashboard/appointments/123)
    return pathname.startsWith(href);
  };

  return (
    <aside
      className={cn(
        "h-full bg-muted/40 border-r border-border flex flex-col transition-all duration-300 ease-in-out backdrop-blur-sm supports-[backdrop-filter]:bg-muted/40 relative",
        collapsed ? "w-sidebar-collapsed" : "w-sidebar",
        className
      )}
    >
      {/* Logo */}
      <div className="h-topbar flex items-center px-4 border-b border-border bg-background/50 backdrop-blur-sm">
        <Link href="/" target="_self" className="flex items-center gap-3 group">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm group-hover:shadow transition-all">
            <Hospital className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col animate-in fade-in slide-in-from-left-2 duration-300">
              <span className="font-bold text-foreground leading-tight">HealthPRM</span>
              <span className="text-[10px] uppercase tracking-wider text-blue-600 font-semibold">Surya Hospitals</span>
            </div>
          )}
        </Link>
      </div>

      {/* Toggle Button - Floating on the separator */}
      <button
        onClick={toggleCollapsed}
        className="absolute -right-3 top-6 z-50 p-1 bg-background border border-border rounded-full shadow-sm text-muted-foreground hover:text-blue-600 hover:border-blue-200 transition-colors"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? (
          <ChevronsRight className="w-3 h-3" />
        ) : (
          <ChevronsLeft className="w-3 h-3" />
        )}
      </button>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-6 scrollbar-hide">
        {navigationConfig.map((section) => (
          <div key={section.id}>
            {/* Section Header */}
            {!collapsed && (
              <div className="px-3 mb-2">
                {section.collapsible ? (
                  <button
                    onClick={() => toggleSection(section.id)}
                    className="flex items-center justify-between w-full text-xs font-semibold text-muted-foreground uppercase tracking-wider hover:text-foreground transition-colors group"
                  >
                    <span>{section.title}</span>
                    <span className="opacity-0 group-hover:opacity-100 transition-opacity">
                      {collapsedSections.has(section.id) ? (
                        <ChevronRight className="w-3 h-3" />
                      ) : (
                        <ChevronDown className="w-3 h-3" />
                      )}
                    </span>
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
                      target="_self"
                      className={cn(
                        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all relative group",
                        active
                          ? "bg-background text-blue-700 shadow-sm ring-1 ring-border"
                          : "text-muted-foreground hover:bg-accent hover:text-foreground",
                        collapsed && "justify-center px-2"
                      )}
                      title={collapsed ? item.label : undefined}
                    >
                      <item.icon className={cn("w-5 h-5 shrink-0 transition-colors", active ? "text-blue-600" : "text-muted-foreground group-hover:text-foreground")} />

                      {!collapsed && (
                        <>
                          <span className="flex-1 truncate">{item.label}</span>
                          {badgeValue !== undefined && badgeValue > 0 && (
                            <Badge variant="secondary" className="ml-auto text-xs h-5 min-w-5 flex items-center justify-center bg-blue-100 text-blue-700 hover:bg-blue-100">
                              {badgeValue > 99 ? "99+" : badgeValue}
                            </Badge>
                          )}
                        </>
                      )}

                      {/* Tooltip for collapsed state */}
                      {collapsed && (
                        <div className="absolute left-full ml-2 px-2 py-1 bg-foreground text-background text-xs rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap z-50">
                          {item.label}
                          {badgeValue !== undefined && badgeValue > 0 && (
                            <span className="ml-2 inline-flex items-center justify-center bg-blue-500 text-white rounded-full h-4 min-w-[1rem] px-1">
                              {badgeValue}
                            </span>
                          )}
                        </div>
                      )}
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </nav>


    </aside>
  );
}

export default Sidebar;
