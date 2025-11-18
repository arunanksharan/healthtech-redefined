"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  Calendar,
  MessageSquare,
  Users,
  Ticket,
  Route,
  Settings,
  Menu,
  X,
  Mic,
  Command as CommandIcon,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { AIChat, CommandBar } from "@/components/ai";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Users },
  { name: "Patients", href: "/dashboard/patients", icon: Users },
  { name: "Appointments", href: "/dashboard/appointments", icon: Calendar },
  { name: "Journeys", href: "/dashboard/journeys", icon: Route },
  { name: "Communications", href: "/dashboard/communications", icon: MessageSquare },
  { name: "Tickets", href: "/dashboard/tickets", icon: Ticket },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [aiPanelOpen, setAiPanelOpen] = useState(true);
  const [commandBarOpen, setCommandBarOpen] = useState(false);
  const pathname = usePathname();

  // Demo user context - replace with actual auth context
  const userId = "user_123";
  const orgId = "org_456";
  const sessionId = `session_${Date.now()}`;
  const permissions = ["appointments.read", "appointments.write", "patients.read", "patients.write"];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-2 px-6 py-5 border-b border-gray-200">
            <Bot className="w-8 h-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-900">PRM</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-600"
                      : "text-gray-700 hover:bg-gray-100"
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Quick Actions */}
          <div className="p-4 border-t border-gray-200">
            <button
              onClick={() => setCommandBarOpen(true)}
              className="flex items-center justify-center gap-2 w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <CommandIcon className="w-4 h-4" />
              Command (⌘K)
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 left-4 z-50 lg:hidden p-2 bg-white rounded-lg shadow-lg"
      >
        {sidebarOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <Menu className="w-6 h-6" />
        )}
      </button>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-semibold text-gray-900">
              {navigation.find((item) => item.href === pathname)?.name || "Dashboard"}
            </h1>

            <div className="flex items-center gap-4">
              <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
                <Mic className="w-5 h-5" />
              </button>
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full" />
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>

      {/* AI Assistant Panel */}
      {aiPanelOpen && (
        <aside className="hidden xl:block w-96 bg-white border-l border-gray-200">
          <AIChat
            userId={userId}
            orgId={orgId}
            sessionId={sessionId}
            permissions={permissions}
          />
        </aside>
      )}

      {/* Command Bar (Cmd+K) */}
      {commandBarOpen && (
        <CommandBar
          userId={userId}
          orgId={orgId}
          sessionId={sessionId}
          permissions={permissions}
        />
      )}

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
