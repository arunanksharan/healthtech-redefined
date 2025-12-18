"use client";

import * as React from "react";
import { createContext, useContext, useEffect, useState } from "react";

type Theme = "dark" | "light" | "system";

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
  attribute?: string;
  enableSystem?: boolean;
  disableTransitionOnChange?: boolean;
  forcedTheme?: Theme;
}

interface ThemeProviderState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: "dark" | "light";
  forcedTheme?: Theme;
}

const initialState: ThemeProviderState = {
  theme: "system",
  setTheme: () => null,
  resolvedTheme: "light",
};

const ThemeProviderContext = createContext<ThemeProviderState>(initialState);

export function ThemeProvider({
  children,
  defaultTheme = "system",
  storageKey = "prm-ui-theme",
  attribute = "class",
  enableSystem = true,
  disableTransitionOnChange = false,
  forcedTheme,
  ...props
}: ThemeProviderProps) {
  const [theme, setTheme] = useState<Theme>(defaultTheme);
  const [resolvedTheme, setResolvedTheme] = useState<"dark" | "light">("light");
  const [mounted, setMounted] = useState(false);

  // Get system preference
  const getSystemTheme = (): "dark" | "light" => {
    if (typeof window === "undefined") return "light";
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  };

  // Resolve the actual theme
  const resolveTheme = (t: Theme): "dark" | "light" => {
    if (t === "system") {
      return getSystemTheme();
    }
    return t;
  };

  // Initialize theme from storage (only if not forced)
  useEffect(() => {
    if (forcedTheme) {
      setMounted(true);
      return;
    }
    const savedTheme = localStorage.getItem(storageKey) as Theme | null;
    if (savedTheme) {
      setTheme(savedTheme);
    }
    setMounted(true);
  }, [storageKey, forcedTheme]);

  // Update resolved theme and apply to document
  useEffect(() => {
    if (!mounted) return;

    // If forced, use forced theme; otherwise use user preference
    const themeToUse = forcedTheme || theme;
    const resolved = resolveTheme(themeToUse);
    setResolvedTheme(resolved);

    const root = window.document.documentElement;

    // Disable transitions if needed
    if (disableTransitionOnChange) {
      root.style.setProperty("transition", "none");
    }

    // Remove old theme class and add new one
    root.classList.remove("light", "dark");
    if (attribute === "class") {
      root.classList.add(resolved);
    } else {
      root.setAttribute(attribute, resolved);
    }

    // Re-enable transitions
    if (disableTransitionOnChange) {
      // Force reflow
      void root.offsetWidth;
      root.style.removeProperty("transition");
    }
  }, [theme, mounted, attribute, disableTransitionOnChange, forcedTheme]);

  // Listen for system theme changes
  useEffect(() => {
    if (!enableSystem || theme !== "system") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      setResolvedTheme(getSystemTheme());
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [theme, enableSystem]);

  const value = {
    theme: forcedTheme || theme,
    setTheme: (newTheme: Theme) => {
      // Don't save to localStorage if theme is forced
      if (forcedTheme) return;
      localStorage.setItem(storageKey, newTheme);
      setTheme(newTheme);
    },
    resolvedTheme,
    forcedTheme,
  };

  // Prevent flash of incorrect theme
  if (!mounted) {
    return (
      <ThemeProviderContext.Provider {...props} value={value}>
        <div style={{ visibility: "hidden" }}>{children}</div>
      </ThemeProviderContext.Provider>
    );
  }

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
}

export const useTheme = () => {
  const context = useContext(ThemeProviderContext);

  if (context === undefined)
    throw new Error("useTheme must be used within a ThemeProvider");

  return context;
};
