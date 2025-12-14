"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { Bot, Calendar, MessageSquare, Shield } from "lucide-react";
import { DotPattern } from "@/components/ui/dot-pattern";
import { cn } from "@/lib/utils";
import { WordRotate } from "@/components/ui/word-rotate";
import { ShimmerButton } from "@/components/ui/shimmer-button";
import { BentoGrid, BentoCard } from "@/components/ui/bento-grid";
import { MagicCard } from "@/components/ui/magic-card";
import {
  AITypingAnimation,
  CalendarAnimation,
  ChatBubblesAnimation,
  SecurityAnimation
} from "@/components/ui/bento-animations";

export default function HomePage() {
  const previousTheme = useRef<string | null>(null);

  // Force light mode on homepage
  useEffect(() => {
    const root = window.document.documentElement;

    // Save current theme
    previousTheme.current = root.classList.contains("dark") ? "dark" : "light";

    // Force light mode
    root.classList.remove("dark");
    root.classList.add("light");

    // Restore previous theme when leaving
    return () => {
      const savedTheme = localStorage.getItem("prm-ui-theme");
      if (savedTheme === "dark") {
        root.classList.remove("light");
        root.classList.add("dark");
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-white text-gray-900 overflow-hidden relative selection:bg-blue-100">
      <DotPattern
        width={20}
        height={20}
        cx={1}
        cy={1}
        cr={1}
        className={cn(
          "fill-gray-300/40"
        )}
      />

      {/* Radiant Background Blobs */}
      <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
      <div className="absolute top-0 -right-4 w-72 h-72 bg-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-8 left-20 w-72 h-72 bg-teal-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>

      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16 md:py-32 relative z-10">
        <div className="text-center max-w-5xl mx-auto space-y-8">
          <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 px-4 py-2 rounded-full text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors cursor-default">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            System Operational
          </div>

          <div className="flex flex-col items-center justify-center">
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-gray-900 mb-4">
              Healthcare Redefined by
            </h1>
            <WordRotate
              className="text-5xl md:text-7xl font-bold tracking-tight text-blue-600"
              words={["Intelligence", "Automation", "Speed", "Empathy"]}
            />
          </div>

          <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Revolutionary Patient Relationship Management.
            <br />
            No menus, no forms. Just natural language.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-8">
            <Link href="/dashboard">
              <ShimmerButton
                background="#2563EB" // blue-600
                shimmerColor="#93C5FD" // blue-300
                className="shadow-lg shadow-blue-500/20"
              >
                <span className="whitespace-pre-wrap text-center text-sm font-medium leading-none tracking-tight text-white lg:text-lg">
                  Open Dashboard
                </span>
              </ShimmerButton>
            </Link>
          </div>
        </div>

        {/* Features Bento Grid */}
        <div className="mt-32">
          <BentoGrid className="max-w-6xl mx-auto grid-cols-1 md:grid-cols-3 gap-8">
            <BentoCard
              name="AI-First Interface"
              description="Talk to specialized agents using natural language. No clicking through menus."
              background={<AITypingAnimation />}
              Icon={Bot}
              className="md:col-span-2 bg-white border border-gray-200 shadow-md hover:shadow-xl transition-all"
              href="/dashboard"
              cta="Open Agent"
            />
            <BentoCard
              name="Smart Scheduling"
              description="Book appointments, reschedule, and send reminders with a single command."
              background={<CalendarAnimation />}
              Icon={Calendar}
              className="md:col-span-1 bg-white border border-gray-200 shadow-md hover:shadow-xl transition-all"
              href="/dashboard/appointments"
              cta="Manage Calendar"
            />
            <BentoCard
              name="Unified Comms"
              description="WhatsApp, SMS, Email - all managed through one AI assistant."
              background={<ChatBubblesAnimation />}
              Icon={MessageSquare}
              className="md:col-span-1 bg-white border border-gray-200 shadow-md hover:shadow-xl transition-all"
              href="/dashboard/communications"
              cta="View Inbox"
            />
            <BentoCard
              name="Secure & Compliant"
              description="Enterprise-grade security with HIPAA compliance built-in."
              background={<SecurityAnimation />}
              Icon={Shield}
              className="md:col-span-2 bg-white border border-gray-200 shadow-md hover:shadow-xl transition-all"
              href="/dashboard/settings"
              cta="Security Settings"
            />
          </BentoGrid>
        </div>

        {/* Live Stats */}
        <div className="mt-16 md:mt-32 max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:h-[200px]">
            <MagicCard
              className="flex flex-col items-center justify-center p-6 bg-white border border-gray-200 shadow-md"
              gradientColor="#D1D5DB" // gray-300 for visible border gradient
              gradientOpacity={0.4}
              gradientFrom="#BFDBFE" // blue-200
              gradientTo="#99F6E4"   // teal-200
            >
              <div className="text-4xl font-bold text-gray-900 mb-2">95%</div>
              <div className="text-sm text-gray-500 uppercase tracking-widest">Intent Accuracy</div>
            </MagicCard>
            <MagicCard
              className="flex flex-col items-center justify-center p-6 bg-white border border-gray-200 shadow-md"
              gradientColor="#D1D5DB"
              gradientOpacity={0.4}
              gradientFrom="#BFDBFE"
              gradientTo="#99F6E4"
            >
              <div className="text-4xl font-bold text-gray-900 mb-2">&lt;2s</div>
              <div className="text-sm text-gray-500 uppercase tracking-widest">Response Time</div>
            </MagicCard>
            <MagicCard
              className="flex flex-col items-center justify-center p-6 bg-white border border-gray-200 shadow-md"
              gradientColor="#D1D5DB"
              gradientOpacity={0.4}
              gradientFrom="#BFDBFE"
              gradientTo="#99F6E4"
            >
              <div className="text-4xl font-bold text-gray-900 mb-2">24/7</div>
              <div className="text-sm text-gray-500 uppercase tracking-widest">Availability</div>
            </MagicCard>
            <MagicCard
              className="flex flex-col items-center justify-center p-6 bg-white border border-gray-200 shadow-md"
              gradientColor="#D1D5DB"
              gradientOpacity={0.4}
              gradientFrom="#BFDBFE"
              gradientTo="#99F6E4"
            >
              <div className="text-4xl font-bold text-gray-900 mb-2">10x</div>
              <div className="text-sm text-gray-500 uppercase tracking-widest">Productivity</div>
            </MagicCard>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-32 pb-8 text-center text-gray-400 text-sm">
          <p>© 2024 Kuzushi HealthTech. All rights reserved.</p>
        </footer>
      </div>
    </div>
  );
}
