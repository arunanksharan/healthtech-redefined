"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Users,
  Calendar,
  Inbox,
  Menu,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Badge } from "@/components/ui/badge";

interface MobileNavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  badge?: number;
}

const navItems: MobileNavItem[] = [
  { id: "home", label: "Home", icon: Home, href: "/dashboard" },
  { id: "patients", label: "Patients", icon: Users, href: "/dashboard/patients" },
  { id: "schedule", label: "Schedule", icon: Calendar, href: "/dashboard/appointments" },
  { id: "inbox", label: "Inbox", icon: Inbox, href: "/inbox", badge: 12 },
  { id: "more", label: "More", icon: Menu, href: "/dashboard/settings" },
];

interface MobileNavProps {
  className?: string;
  onMoreClick?: () => void;
}

export function MobileNav({ className, onMoreClick }: MobileNavProps) {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/" || pathname === "/dashboard";
    }
    return pathname.startsWith(href);
  };

  return (
    <nav
      className={cn(
        "fixed bottom-0 left-0 right-0 z-50",
        "bg-card border-t border-border",
        "safe-area-bottom",
        "md:hidden",
        className
      )}
    >
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item) => {
          const active = isActive(item.href);
          const isMore = item.id === "more";

          const content = (
            <div
              className={cn(
                "flex flex-col items-center justify-center flex-1 h-full gap-0.5",
                "text-xs transition-colors min-w-0 py-1",
                active ? "text-primary" : "text-muted-foreground"
              )}
            >
              <div className="relative">
                <item.icon
                  className={cn(
                    "w-5 h-5 transition-transform",
                    active && "scale-110"
                  )}
                />
                {item.badge !== undefined && item.badge > 0 && (
                  <span className="absolute -top-1 -right-2 min-w-4 h-4 bg-destructive text-destructive-foreground text-[10px] rounded-full flex items-center justify-center px-1">
                    {item.badge > 99 ? "99+" : item.badge}
                  </span>
                )}
              </div>
              <span className="truncate">{item.label}</span>
              {active && (
                <span className="absolute bottom-0 w-8 h-0.5 bg-primary rounded-full" />
              )}
            </div>
          );

          if (isMore) {
            return (
              <button
                key={item.id}
                onClick={onMoreClick}
                className="relative flex-1 h-full"
              >
                {content}
              </button>
            );
          }

          return (
            <Link
              key={item.id}
              href={item.href}
              className="relative flex-1 h-full"
            >
              {content}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export default MobileNav;
