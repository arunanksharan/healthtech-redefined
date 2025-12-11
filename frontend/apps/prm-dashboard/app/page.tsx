"use client";

import Link from "next/link";
import { Bot, Calendar, MessageSquare, Shield } from "lucide-react";
import { GridPattern } from "@/components/ui/grid-pattern";
import { WordRotate } from "@/components/ui/word-rotate";
import { ShimmerButton } from "@/components/ui/shimmer-button";
import { BentoGrid, BentoCard } from "@/components/ui/bento-grid";
import { MagicCard } from "@/components/ui/magic-card";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white text-gray-900 overflow-hidden relative selection:bg-blue-100">
      <GridPattern
        width={30}
        height={30}
        x={-1}
        y={-1}
        strokeDasharray={"4 2"}
        className="[mask-image:radial-gradient(500px_circle_at_center,white,transparent)] inset-x-0 inset-y-[-30%] h-[200%] skew-y-12 fill-blue-50 stroke-blue-100"
      />

      {/* Hero Section */}
      <div className="container mx-auto px-4 py-32 relative z-10">
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
              background={<div className="absolute inset-0 bg-blue-50 opacity-100 transition-opacity group-hover:opacity-50" />}
              Icon={Bot}
              className="md:col-span-2 bg-white border border-gray-200 shadow-md hover:shadow-xl transition-all"
              href="/dashboard"
              cta="Open Agent"
            />
            <BentoCard
              name="Smart Scheduling"
              description="Book appointments, reschedule, and send reminders with a single command."
              background={<div className="absolute inset-0 bg-purple-50 opacity-100 transition-opacity group-hover:opacity-50" />}
              Icon={Calendar}
              className="md:col-span-1 bg-white border border-gray-200 shadow-md hover:shadow-xl transition-all"
              href="/dashboard/appointments"
              cta="Manage Calendar"
            />
            <BentoCard
              name="Unified Comms"
              description="WhatsApp, SMS, Email - all managed through one AI assistant."
              background={<div className="absolute inset-0 bg-green-50 opacity-100 transition-opacity group-hover:opacity-50" />}
              Icon={MessageSquare}
              className="md:col-span-1 bg-white border border-gray-200 shadow-md hover:shadow-xl transition-all"
              href="/dashboard/communications"
              cta="View Inbox"
            />
            <BentoCard
              name="Secure & Compliant"
              description="Enterprise-grade security with HIPAA compliance built-in."
              background={<div className="absolute inset-0 bg-red-50 opacity-100 transition-opacity group-hover:opacity-50" />}
              Icon={Shield}
              className="md:col-span-2 bg-white border border-gray-200 shadow-md hover:shadow-xl transition-all"
              href="/dashboard/settings"
              cta="Security Settings"
            />
          </BentoGrid>
        </div>

        {/* Live Stats */}
        <div className="mt-32 max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 h-[200px]">
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
