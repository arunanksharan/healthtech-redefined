"use client";

import * as React from "react";
import { useEffect, useState } from "react";
import {
  Route,
  Phone,
  Activity,
  Clock,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Eye,
  Edit,
  Trash2,
  Power,
  PowerOff,
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
import { useAdminStore, ZoicePipeline } from "@/lib/store/admin-store";
import { zoicePipelinesAPI, ZoicePipelineResponse } from "@/lib/api/zoice";
import { formatDistanceToNow } from "date-fns";

interface PipelineListProps {
  viewMode?: "list" | "grid";
  onPipelineSelect?: (pipeline: ZoicePipeline) => void;
  onCreateClick?: () => void;
}

const statusConfig = {
  active: { label: "Active", variant: "default" as const, className: "bg-green-500 text-white" },
  inactive: { label: "Inactive", variant: "secondary" as const, className: "bg-gray-400 text-white" },
  draft: { label: "Draft", variant: "outline" as const, className: "bg-yellow-500 text-white" },
};

const pipelineTypeConfig = {
  realtime: { label: "Realtime", icon: Activity, className: "text-purple-500" },
  turn_based: { label: "Turn-based", icon: Clock, className: "text-blue-500" },
};

export function PipelineList({ viewMode = "list", onPipelineSelect, onCreateClick }: PipelineListProps) {
  const {
    pipelines,
    isLoadingPipelines,
    pipelinesError,
    setPipelines,
    setLoadingPipelines,
    setPipelinesError,
    updatePipeline,
    removePipeline,
  } = useAdminStore();

  const [refreshing, setRefreshing] = useState(false);

  // Fetch pipelines on mount
  useEffect(() => {
    fetchPipelines();
  }, []);

  const fetchPipelines = async () => {
    setLoadingPipelines(true);
    setPipelinesError(null);
    try {
      const [response, error] = await zoicePipelinesAPI.getAll();
      if (error) {
        setPipelinesError(error.message);
      } else if (response?.data) {
        // Map API response to store format
        const mapped: ZoicePipeline[] = response.data.map((p: ZoicePipelineResponse) => ({
          id: p.id,
          name: p.name,
          description: p.description,
          pipeline_type: p.pipeline_type,
          status: p.status,
          agent_id: p.agent_id,
          phone_numbers: p.phone_numbers,
          created_at: p.created_at,
          updated_at: p.updated_at,
        }));
        setPipelines(mapped);
      }
    } catch (err) {
      setPipelinesError("Failed to fetch pipelines");
    } finally {
      setLoadingPipelines(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchPipelines();
    setRefreshing(false);
  };

  const handleToggleStatus = async (pipeline: ZoicePipeline) => {
    const newStatus = pipeline.status === "active" ? "inactive" : "active";
    try {
      const [response, error] = await zoicePipelinesAPI.update(pipeline.id, { status: newStatus });
      if (!error && response) {
        updatePipeline(pipeline.id, { status: newStatus });
      }
    } catch (err) {
      console.error("Failed to toggle pipeline status:", err);
    }
  };

  const handleDelete = async (pipeline: ZoicePipeline) => {
    if (!confirm(`Are you sure you want to delete "${pipeline.name}"?`)) return;
    try {
      const [response, error] = await zoicePipelinesAPI.delete(pipeline.id);
      if (!error) {
        removePipeline(pipeline.id);
      }
    } catch (err) {
      console.error("Failed to delete pipeline:", err);
    }
  };

  // Table columns definition
  const columns: Column<ZoicePipeline>[] = [
    {
      id: "name",
      header: "Pipeline",
      accessorKey: "name",
      sortable: true,
      cell: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
            <Route className="w-4 h-4 text-purple-500" />
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
      id: "type",
      header: "Type",
      accessorKey: "pipeline_type",
      sortable: true,
      cell: (row) => {
        const config = pipelineTypeConfig[row.pipeline_type];
        const Icon = config.icon;
        return (
          <div className="flex items-center gap-2">
            <Icon className={cn("w-4 h-4", config.className)} />
            <span className="text-sm">{config.label}</span>
          </div>
        );
      },
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      sortable: true,
      cell: (row) => {
        const config = statusConfig[row.status];
        return (
          <Badge className={cn("text-xs", config.className)}>
            {config.label}
          </Badge>
        );
      },
    },
    {
      id: "phone_numbers",
      header: "Phone Numbers",
      cell: (row) => (
        <div className="flex items-center gap-1">
          <Phone className="w-4 h-4 text-gray-400" />
          <span className="text-sm">{row.phone_numbers?.length || 0}</span>
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

  // Grid view card
  const PipelineCard = ({ pipeline }: { pipeline: ZoicePipeline }) => {
    const statusCfg = statusConfig[pipeline.status];
    const typeCfg = pipelineTypeConfig[pipeline.pipeline_type];
    const TypeIcon = typeCfg.icon;

    return (
      <Card
        className="hover:shadow-lg transition-all duration-200 cursor-pointer group"
        onClick={() => onPipelineSelect?.(pipeline)}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Route className="w-5 h-5 text-purple-500" />
              </div>
              <div>
                <CardTitle className="text-base">{pipeline.name}</CardTitle>
                <div className="flex items-center gap-2 mt-1">
                  <TypeIcon className={cn("w-3 h-3", typeCfg.className)} />
                  <span className="text-xs text-gray-500">{typeCfg.label}</span>
                </div>
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onPipelineSelect?.(pipeline); }}>
                  <Eye className="w-4 h-4 mr-2" />
                  View Details
                </DropdownMenuItem>
                <DropdownMenuItem onClick={(e) => e.stopPropagation()}>
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleToggleStatus(pipeline); }}>
                  {pipeline.status === "active" ? (
                    <>
                      <PowerOff className="w-4 h-4 mr-2" />
                      Deactivate
                    </>
                  ) : (
                    <>
                      <Power className="w-4 h-4 mr-2" />
                      Activate
                    </>
                  )}
                </DropdownMenuItem>
                <DropdownMenuItem
                  className="text-destructive"
                  onClick={(e) => { e.stopPropagation(); handleDelete(pipeline); }}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        <CardContent>
          {pipeline.description && (
            <CardDescription className="mb-3 line-clamp-2">
              {pipeline.description}
            </CardDescription>
          )}
          <div className="flex items-center justify-between">
            <Badge className={cn("text-xs", statusCfg.className)}>
              {statusCfg.label}
            </Badge>
            <div className="flex items-center gap-1 text-gray-500">
              <Phone className="w-3 h-3" />
              <span className="text-xs">{pipeline.phone_numbers?.length || 0} numbers</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // Loading skeleton for grid
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
            <div className="flex justify-between">
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-4 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  // Error state
  if (pipelinesError) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full mb-4">
          <Route className="w-6 h-6 text-red-500" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Failed to load pipelines</h3>
        <p className="text-gray-500 dark:text-gray-400 mb-4">{pipelinesError}</p>
        <Button onClick={handleRefresh} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Pipelines</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Manage your voice AI pipelines for inbound and outbound calls
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={cn("w-4 h-4 mr-2", refreshing && "animate-spin")} />
            Refresh
          </Button>
          <Button onClick={onCreateClick} className="bg-purple-500 hover:bg-purple-600">
            <Plus className="w-4 h-4 mr-2" />
            Create Pipeline
          </Button>
        </div>
      </div>

      {/* Content */}
      {isLoadingPipelines ? (
        viewMode === "grid" ? (
          <GridSkeleton />
        ) : (
          <DataTable
            data={[]}
            columns={columns}
            keyField="id"
            isLoading={true}
            searchPlaceholder="Search pipelines..."
            searchFields={["name", "description"]}
          />
        )
      ) : viewMode === "grid" ? (
        pipelines.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-full mb-4">
              <Route className="w-6 h-6 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No pipelines yet</h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">Create your first voice AI pipeline to get started</p>
            <Button onClick={onCreateClick} className="bg-purple-500 hover:bg-purple-600">
              <Plus className="w-4 h-4 mr-2" />
              Create Pipeline
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pipelines.map((pipeline) => (
              <PipelineCard key={pipeline.id} pipeline={pipeline} />
            ))}
          </div>
        )
      ) : (
        <DataTable
          data={pipelines}
          columns={columns}
          keyField="id"
          onRowClick={onPipelineSelect}
          searchPlaceholder="Search pipelines..."
          searchFields={["name", "description"]}
          statusTabs={[
            { value: null, label: "All", count: pipelines.length },
            { value: "active", label: "Active", count: pipelines.filter((p) => p.status === "active").length },
            { value: "inactive", label: "Inactive", count: pipelines.filter((p) => p.status === "inactive").length },
            { value: "draft", label: "Draft", count: pipelines.filter((p) => p.status === "draft").length },
          ]}
          emptyMessage="No pipelines found"
        />
      )}
    </div>
  );
}

export default PipelineList;
