"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";

interface ContextPanelProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  onClose: () => void;
  className?: string;
  width?: "sm" | "md" | "lg" | "xl";
  headerActions?: React.ReactNode;
  footer?: React.ReactNode;
}

const widthClasses = {
  sm: "w-72",
  md: "w-80",
  lg: "w-96",
  xl: "w-[420px]",
};

export function ContextPanel({
  children,
  title,
  subtitle,
  onClose,
  className,
  width = "lg",
  headerActions,
  footer,
}: ContextPanelProps) {
  // Handle escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  return (
    <aside
      className={cn(
        "fixed right-0 top-topbar h-[calc(100vh-var(--topbar-height))]",
        "bg-card border-l border-border",
        "flex flex-col overflow-hidden",
        "animate-slide-in-from-right shadow-xl",
        widthClasses[width],
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-border shrink-0">
        <div className="flex-1 min-w-0">
          {title && (
            <h2 className="text-lg font-semibold text-foreground truncate">
              {title}
            </h2>
          )}
          {subtitle && (
            <p className="text-sm text-muted-foreground mt-0.5 truncate">
              {subtitle}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4 shrink-0">
          {headerActions}
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
            aria-label="Close panel"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">{children}</div>

      {/* Footer */}
      {footer && (
        <div className="shrink-0 p-4 border-t border-border bg-muted/30">
          {footer}
        </div>
      )}
    </aside>
  );
}

// Simple wrapper for panel sections
interface PanelSectionProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export function PanelSection({
  title,
  children,
  className,
  action,
}: PanelSectionProps) {
  return (
    <div className={cn("mb-6 last:mb-0", className)}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-3">
          {title && (
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              {title}
            </h3>
          )}
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

// Panel info row component
interface PanelInfoRowProps {
  label: string;
  value: React.ReactNode;
  className?: string;
}

export function PanelInfoRow({ label, value, className }: PanelInfoRowProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between py-2 border-b border-border last:border-0",
        className
      )}
    >
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

export default ContextPanel;
