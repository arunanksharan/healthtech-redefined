"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { Bot, Calendar, MessageSquare, Shield, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { WordRotate } from "@/components/ui/word-rotate";

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
      {/* Geometric Background Decorations */}
      <div className="absolute top-20 -left-32 w-96 h-96 rounded-full bg-blue-500/5" />
      <div className="absolute top-40 right-20 w-64 h-64 bg-emerald-500/5 rotate-45" />
      <div className="absolute bottom-40 left-1/4 w-48 h-48 rounded-full bg-amber-500/5" />
      <div className="absolute -bottom-20 right-1/3 w-80 h-80 bg-gray-100 rotate-12" />

      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16 md:py-32 relative z-10 max-w-7xl">
        <div className="text-center max-w-5xl mx-auto space-y-8">
          {/* Status Badge - Flat solid style */}
          <div className="inline-flex items-center gap-2 bg-blue-500 px-5 py-2.5 rounded-full text-sm font-medium text-white">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
            </span>
            System Operational
          </div>

          {/* Main Heading - Outfit font */}
          <div className="flex flex-col items-center justify-center">
            <h1 className="font-heading text-5xl md:text-7xl text-gray-900 mb-4">
              Healthcare Redefined by
            </h1>
            <WordRotate
              className="font-heading text-5xl md:text-7xl text-blue-500"
              words={["Intelligence", "Automation", "Speed", "Empathy"]}
            />
          </div>

          {/* Subheadline */}
          <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Revolutionary Patient Relationship Management.
            <br />
            No menus, no forms. Just natural language.
          </p>

          {/* CTA Button - Flat solid with scale hover */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-8">
            <Link href="/dashboard">
              <button className="flat-btn-primary text-lg flex items-center gap-2 group">
                Open Dashboard
                <ArrowRight className="w-5 h-5 transition-transform duration-200 group-hover:translate-x-1" />
              </button>
            </Link>
          </div>
        </div>

        {/* Features Section - Flat Color Blocks */}
        <div className="mt-32">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {/* AI-First Interface - Blue tint, spans 2 cols */}
            <Link
              href="/dashboard"
              className="md:col-span-2 group cursor-pointer"
            >
              <div className="flat-card bg-blue-50 hover:bg-blue-100 h-full">
                <div className="flex items-start gap-4">
                  <div className="w-14 h-14 rounded-full bg-white flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
                    <Bot className="w-7 h-7 text-blue-500" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-heading text-xl text-gray-900 mb-2">
                      AI-First Interface
                    </h3>
                    <p className="text-gray-600">
                      Talk to specialized agents using natural language. No clicking through menus.
                    </p>
                  </div>
                </div>
                <div className="mt-6 flex items-center text-blue-500 font-semibold text-sm uppercase tracking-wider">
                  Open Agent
                  <ArrowRight className="w-4 h-4 ml-2 transition-transform duration-200 group-hover:translate-x-1" />
                </div>
              </div>
            </Link>

            {/* Smart Scheduling - Emerald tint */}
            <Link href="/dashboard/appointments" className="group cursor-pointer">
              <div className="flat-card bg-emerald-50 hover:bg-emerald-100 h-full">
                <div className="flex items-start gap-4">
                  <div className="w-14 h-14 rounded-full bg-white flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
                    <Calendar className="w-7 h-7 text-emerald-500" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-heading text-xl text-gray-900 mb-2">
                      Smart Scheduling
                    </h3>
                    <p className="text-gray-600">
                      Book, reschedule, and send reminders with a single command.
                    </p>
                  </div>
                </div>
                <div className="mt-6 flex items-center text-emerald-500 font-semibold text-sm uppercase tracking-wider">
                  Manage Calendar
                  <ArrowRight className="w-4 h-4 ml-2 transition-transform duration-200 group-hover:translate-x-1" />
                </div>
              </div>
            </Link>

            {/* Unified Comms - Amber tint */}
            <Link href="/dashboard/communications" className="group cursor-pointer">
              <div className="flat-card bg-amber-50 hover:bg-amber-100 h-full">
                <div className="flex items-start gap-4">
                  <div className="w-14 h-14 rounded-full bg-white flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
                    <MessageSquare className="w-7 h-7 text-amber-500" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-heading text-xl text-gray-900 mb-2">
                      Unified Comms
                    </h3>
                    <p className="text-gray-600">
                      WhatsApp, SMS, Email - all managed through one AI assistant.
                    </p>
                  </div>
                </div>
                <div className="mt-6 flex items-center text-amber-500 font-semibold text-sm uppercase tracking-wider">
                  View Inbox
                  <ArrowRight className="w-4 h-4 ml-2 transition-transform duration-200 group-hover:translate-x-1" />
                </div>
              </div>
            </Link>

            {/* Secure & Compliant - Gray tint, spans 2 cols */}
            <Link
              href="/dashboard/settings"
              className="md:col-span-2 group cursor-pointer"
            >
              <div className="flat-card bg-gray-100 hover:bg-gray-200 h-full">
                <div className="flex items-start gap-4">
                  <div className="w-14 h-14 rounded-full bg-white flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
                    <Shield className="w-7 h-7 text-gray-700" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-heading text-xl text-gray-900 mb-2">
                      Secure & Compliant
                    </h3>
                    <p className="text-gray-600">
                      Enterprise-grade security with HIPAA compliance built-in.
                    </p>
                  </div>
                </div>
                <div className="mt-6 flex items-center text-gray-700 font-semibold text-sm uppercase tracking-wider">
                  Security Settings
                  <ArrowRight className="w-4 h-4 ml-2 transition-transform duration-200 group-hover:translate-x-1" />
                </div>
              </div>
            </Link>
          </div>
        </div>

        {/* Stats Section - Gray background block with multi-color stats */}
        <div className="mt-24 -mx-4 md:-mx-8 lg:-mx-16">
          <div className="bg-gray-100 py-16 px-4">
            <div className="max-w-6xl mx-auto">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {/* Stat 1 - Blue */}
                <div className="flat-card bg-white text-center">
                  <div className="font-heading text-5xl text-blue-500 mb-2">95%</div>
                  <div className="text-sm text-gray-500 uppercase tracking-widest font-medium">
                    Intent Accuracy
                  </div>
                </div>

                {/* Stat 2 - Emerald */}
                <div className="flat-card bg-white text-center">
                  <div className="font-heading text-5xl text-emerald-500 mb-2">&lt;2s</div>
                  <div className="text-sm text-gray-500 uppercase tracking-widest font-medium">
                    Response Time
                  </div>
                </div>

                {/* Stat 3 - Amber */}
                <div className="flat-card bg-white text-center">
                  <div className="font-heading text-5xl text-amber-500 mb-2">24/7</div>
                  <div className="text-sm text-gray-500 uppercase tracking-widest font-medium">
                    Availability
                  </div>
                </div>

                {/* Stat 4 - Purple */}
                <div className="flat-card bg-white text-center">
                  <div className="font-heading text-5xl text-purple-500 mb-2">10x</div>
                  <div className="text-sm text-gray-500 uppercase tracking-widest font-medium">
                    Productivity
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer - Dark gray block */}
        <div className="mt-0 -mx-4 md:-mx-8 lg:-mx-16">
          <div className="bg-gray-900 py-12 px-4">
            <div className="max-w-6xl mx-auto text-center">
              <p className="text-gray-400 text-sm">
                © 2024 Kuzushi HealthTech. All rights reserved.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
