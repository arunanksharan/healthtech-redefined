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
  Hospital,
  Microscope,
  Stethoscope,
  Pill,
  FlaskConical,
  BarChart3,
  MessageSquare,
  Video,
  CreditCard,
  ChevronDown,
  ChevronRight,
  Route,
  Ticket,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

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
  forceCollapsed?: boolean;
}

export function Sidebar({ className, onCollapsedChange, forceCollapsed }: SidebarProps) {
  const pathname = usePathname();
  const badges = useBadgeCounts();

  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());

  const collapsed = forceCollapsed !== undefined ? forceCollapsed : internalCollapsed;

  const toggleCollapsed = useCallback(() => {
    setInternalCollapsed((prev) => {
      const newValue = !prev;
      setTimeout(() => onCollapsedChange?.(newValue), 0);
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
    if (href === "/" || href === "/dashboard") {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <aside
      className={cn(
        "h-full bg-white dark:bg-gray-900 border-r-2 border-gray-100 dark:border-gray-800 flex flex-col transition-all duration-200",
        collapsed ? "w-sidebar-collapsed" : "w-sidebar",
        className
      )}
    >
      {/* Logo - Flat solid blue */}
      <div className="h-topbar flex items-center px-4 border-b-2 border-gray-100 dark:border-gray-800">
        <Link href="/" target="_self" className="flex items-center gap-3 group">
          <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center transition-all duration-200 group-hover:scale-105 group-hover:bg-blue-600">
            <Hospital className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-heading text-lg text-gray-900 dark:text-white leading-tight">HealthPRM</span>
              <span className="text-[10px] uppercase tracking-widest text-blue-500 font-semibold">Surya Hospitals</span>
            </div>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-6 scrollbar-hide">
        {navigationConfig.map((section) => (
          <div key={section.id}>
            {/* Section Header */}
            {!collapsed && (
              <div className="px-3 mb-3">
                {section.collapsible ? (
                  <button
                    onClick={() => toggleSection(section.id)}
                    className="flex items-center justify-between w-full text-xs font-semibold text-gray-400 uppercase tracking-widest hover:text-gray-600 dark:hover:text-gray-300 transition-colors group"
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
                  <span className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
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
                        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 relative group",
                        active
                          ? "bg-blue-500 text-white"
                          : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white",
                        collapsed && "justify-center px-2",
                        !active && "hover:scale-[1.02]"
                      )}
                      title={collapsed ? item.label : undefined}
                    >
                      <item.icon
                        className={cn(
                          "w-5 h-5 shrink-0 transition-all duration-200",
                          active ? "text-white" : "text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300",
                          !active && "group-hover:scale-110"
                        )}
                      />

                      {!collapsed && (
                        <>
                          <span className="flex-1 truncate">{item.label}</span>
                          {badgeValue !== undefined && badgeValue > 0 && (
                            <span
                              className={cn(
                                "ml-auto text-xs font-semibold px-2 py-0.5 rounded-md",
                                active
                                  ? "bg-white/20 text-white"
                                  : "bg-blue-500 text-white"
                              )}
                            >
                              {badgeValue > 99 ? "99+" : badgeValue}
                            </span>
                          )}
                        </>
                      )}

                      {/* Tooltip for collapsed state */}
                      {collapsed && (
                        <div className="absolute left-full ml-3 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50">
                          {item.label}
                          {badgeValue !== undefined && badgeValue > 0 && (
                            <span className="ml-2 inline-flex items-center justify-center bg-blue-500 text-white rounded-md h-5 min-w-[1.25rem] px-1 text-xs font-semibold">
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
