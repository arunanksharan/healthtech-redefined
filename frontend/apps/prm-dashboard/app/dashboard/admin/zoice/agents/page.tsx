"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LayoutGrid, List } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AgentList } from "@/components/zoice-admin";
import { ZoiceAgent } from "@/lib/store/admin-store";
import { cn } from "@/lib/utils/cn";

export default function ZoiceAgentsPage() {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");

  const handleAgentSelect = (agent: ZoiceAgent) => {
    router.push(`/dashboard/admin/zoice/agents/${agent.id}`);
  };

  const handleCreateClick = () => {
    router.push("/dashboard/admin/zoice/agents/new");
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Voice AI Agents</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Configure AI agents for voice conversations
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setViewMode("list")}
            className={cn(
              "h-8 px-3",
              viewMode === "list" && "bg-white dark:bg-gray-700 shadow-sm"
            )}
          >
            <List className="w-4 h-4 mr-2" />
            List
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setViewMode("grid")}
            className={cn(
              "h-8 px-3",
              viewMode === "grid" && "bg-white dark:bg-gray-700 shadow-sm"
            )}
          >
            <LayoutGrid className="w-4 h-4 mr-2" />
            Grid
          </Button>
        </div>
      </div>

      {/* Agent List */}
      <AgentList
        viewMode={viewMode}
        onAgentSelect={handleAgentSelect}
        onCreateClick={handleCreateClick}
      />
    </div>
  );
}
