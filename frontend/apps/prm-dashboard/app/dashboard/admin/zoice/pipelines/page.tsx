"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LayoutGrid, List } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PipelineList } from "@/components/zoice-admin";
import { useAdminStore, ZoicePipeline } from "@/lib/store/admin-store";
import { cn } from "@/lib/utils/cn";

export default function ZoicePipelinesPage() {
  const router = useRouter();
  const { pipelineViewMode, setPipelineViewMode } = useAdminStore();

  const handlePipelineSelect = (pipeline: ZoicePipeline) => {
    router.push(`/dashboard/admin/zoice/pipelines/${pipeline.id}`);
  };

  const handleCreateClick = () => {
    router.push("/dashboard/admin/zoice/pipelines/new");
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Voice AI Pipelines</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Configure and manage your voice AI conversation pipelines
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPipelineViewMode("list")}
            className={cn(
              "h-8 px-3",
              pipelineViewMode === "list" && "bg-white dark:bg-gray-700 shadow-sm"
            )}
          >
            <List className="w-4 h-4 mr-2" />
            List
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPipelineViewMode("grid")}
            className={cn(
              "h-8 px-3",
              pipelineViewMode === "grid" && "bg-white dark:bg-gray-700 shadow-sm"
            )}
          >
            <LayoutGrid className="w-4 h-4 mr-2" />
            Grid
          </Button>
        </div>
      </div>

      {/* Pipeline List */}
      <PipelineList
        viewMode={pipelineViewMode}
        onPipelineSelect={handlePipelineSelect}
        onCreateClick={handleCreateClick}
      />
    </div>
  );
}
