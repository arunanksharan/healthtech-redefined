"use client";

import * as React from "react";
import { useEffect, useState } from "react";
import {
  Bot,
  MessageSquare,
  Languages,
  Volume2,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Eye,
  Edit,
  Trash2,
  Copy,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { DataTable, Column } from "@/components/data-display/data-table";
import { useAdminStore, ZoiceAgent } from "@/lib/store/admin-store";
import { zoiceAgentsAPI, ZoiceAgentResponse } from "@/lib/api/zoice";
import { formatDistanceToNow } from "date-fns";

interface AgentListProps {
  viewMode?: "list" | "grid";
  onAgentSelect?: (agent: ZoiceAgent) => void;
  onCreateClick?: () => void;
}

export function AgentList({ viewMode = "list", onAgentSelect, onCreateClick }: AgentListProps) {
  const {
    agents,
    isLoadingAgents,
    agentsError,
    setAgents,
    setLoadingAgents,
    setAgentsError,
    removeAgent,
  } = useAdminStore();

  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    setLoadingAgents(true);
    setAgentsError(null);
    try {
      const [response, error] = await zoiceAgentsAPI.getAll();
      if (error) {
        setAgentsError(error.message);
      } else if (response?.data) {
        const mapped: ZoiceAgent[] = response.data.map((a: ZoiceAgentResponse) => ({
          id: a.id,
          name: a.name,
          description: a.description,
          system_prompt: a.system_prompt,
          language: a.language,
          voice_id: a.voice_id,
          llm_config_id: a.llm_config_id,
          stt_config_id: a.stt_config_id,
          tts_config_id: a.tts_config_id,
          created_at: a.created_at,
          updated_at: a.updated_at,
        }));
        setAgents(mapped);
      }
    } catch (err) {
      setAgentsError("Failed to fetch agents");
    } finally {
      setLoadingAgents(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAgents();
    setRefreshing(false);
  };

  const handleDelete = async (agent: ZoiceAgent) => {
    if (!confirm(`Are you sure you want to delete "${agent.name}"?`)) return;
    try {
      const [response, error] = await zoiceAgentsAPI.delete(agent.id);
      if (!error) {
        removeAgent(agent.id);
      }
    } catch (err) {
      console.error("Failed to delete agent:", err);
    }
  };

  const handleDuplicate = async (agent: ZoiceAgent) => {
    try {
      const [response, error] = await zoiceAgentsAPI.create({
        name: `${agent.name} (Copy)`,
        description: agent.description,
        system_prompt: agent.system_prompt,
        language: agent.language,
        voice_id: agent.voice_id,
        llm_config_id: agent.llm_config_id,
        stt_config_id: agent.stt_config_id,
        tts_config_id: agent.tts_config_id,
      });
      if (!error) {
        await fetchAgents();
      }
    } catch (err) {
      console.error("Failed to duplicate agent:", err);
    }
  };

  const columns: Column<ZoiceAgent>[] = [
    {
      id: "name",
      header: "Agent",
      accessorKey: "name",
      sortable: true,
      cell: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Bot className="w-4 h-4 text-blue-500" />
          </div>
          <div>
            <p className="font-medium text-gray-900 dark:text-white">{row.name}</p>
            {row.description && (
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-xs">
                {row.description}
              </p>
            )}
          </div>
        </div>
      ),
    },
    {
      id: "language",
      header: "Language",
      accessorKey: "language",
      cell: (row) => (
        <div className="flex items-center gap-2">
          <Languages className="w-4 h-4 text-gray-400" />
          <span className="text-sm">{row.language || "Not set"}</span>
        </div>
      ),
    },
    {
      id: "voice",
      header: "Voice",
      accessorKey: "voice_id",
      cell: (row) => (
        <div className="flex items-center gap-2">
          <Volume2 className="w-4 h-4 text-gray-400" />
          <span className="text-sm">{row.voice_id ? "Configured" : "Not set"}</span>
        </div>
      ),
    },
    {
      id: "system_prompt",
      header: "System Prompt",
      cell: (row) => (
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500 truncate max-w-[200px]">
            {row.system_prompt ? row.system_prompt.substring(0, 50) + "..." : "No prompt"}
          </span>
        </div>
      ),
    },
    {
      id: "updated_at",
      header: "Last Updated",
      accessorKey: "updated_at",
      sortable: true,
      cell: (row) => (
        <span className="text-sm text-gray-500">
          {formatDistanceToNow(new Date(row.updated_at), { addSuffix: true })}
        </span>
      ),
    },
  ];

  const AgentCard = ({ agent }: { agent: ZoiceAgent }) => (
    <Card
      className="hover:shadow-lg transition-all duration-200 cursor-pointer group"
      onClick={() => onAgentSelect?.(agent)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Bot className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <CardTitle className="text-base">{agent.name}</CardTitle>
              {agent.language && (
                <div className="flex items-center gap-1 mt-1">
                  <Languages className="w-3 h-3 text-gray-400" />
                  <span className="text-xs text-gray-500">{agent.language}</span>
                </div>
              )}
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onAgentSelect?.(agent); }}>
                <Eye className="w-4 h-4 mr-2" />
                View Details
              </DropdownMenuItem>
              <DropdownMenuItem onClick={(e) => e.stopPropagation()}>
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleDuplicate(agent); }}>
                <Copy className="w-4 h-4 mr-2" />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive"
                onClick={(e) => { e.stopPropagation(); handleDelete(agent); }}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent>
        {agent.description && (
          <CardDescription className="mb-3 line-clamp-2">
            {agent.description}
          </CardDescription>
        )}
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Volume2 className="w-3 h-3" />
            <span>{agent.voice_id ? "Voice" : "No voice"}</span>
          </div>
          <div className="flex items-center gap-1">
            <MessageSquare className="w-3 h-3" />
            <span>{agent.system_prompt ? "Prompt set" : "No prompt"}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const GridSkeleton = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <Skeleton className="w-10 h-10 rounded-lg" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-3 w-full mb-3" />
            <Skeleton className="h-4 w-24" />
          </CardContent>
        </Card>
      ))}
    </div>
  );

  if (agentsError) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full mb-4">
          <Bot className="w-6 h-6 text-red-500" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Failed to load agents</h3>
        <p className="text-gray-500 dark:text-gray-400 mb-4">{agentsError}</p>
        <Button onClick={handleRefresh} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Agents</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Configure AI agents for voice conversations
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={cn("w-4 h-4 mr-2", refreshing && "animate-spin")} />
            Refresh
          </Button>
          <Button onClick={onCreateClick} className="bg-blue-500 hover:bg-blue-600">
            <Plus className="w-4 h-4 mr-2" />
            Create Agent
          </Button>
        </div>
      </div>

      {isLoadingAgents ? (
        viewMode === "grid" ? <GridSkeleton /> : (
          <DataTable
            data={[]}
            columns={columns}
            keyField="id"
            isLoading={true}
            searchPlaceholder="Search agents..."
            searchFields={["name", "description"]}
          />
        )
      ) : viewMode === "grid" ? (
        agents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-full mb-4">
              <Bot className="w-6 h-6 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No agents yet</h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">Create your first AI agent to get started</p>
            <Button onClick={onCreateClick} className="bg-blue-500 hover:bg-blue-600">
              <Plus className="w-4 h-4 mr-2" />
              Create Agent
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        )
      ) : (
        <DataTable
          data={agents}
          columns={columns}
          keyField="id"
          onRowClick={onAgentSelect}
          searchPlaceholder="Search agents..."
          searchFields={["name", "description"]}
          emptyMessage="No agents found"
        />
      )}
    </div>
  );
}

export default AgentList;
