"use client";

import * as React from "react";
import { useEffect, useState } from "react";
import {
  PhoneCall,
  PhoneIncoming,
  PhoneOutgoing,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  MoreHorizontal,
  RefreshCw,
  Eye,
  FileText,
  Play,
  Download,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DataTable, Column } from "@/components/data-display/data-table";
import { useAdminStore, ZoiceCall } from "@/lib/store/admin-store";
import { zoiceCallsAPI, ZoiceCallResponse } from "@/lib/api/zoice";
import { format, formatDistanceToNow } from "date-fns";

interface CallListProps {
  onCallSelect?: (call: ZoiceCall) => void;
}

const callStatusConfig = {
  queued: { label: "Queued", icon: Clock, className: "bg-yellow-500 text-white" },
  in_progress: { label: "In Progress", icon: PhoneCall, className: "bg-blue-500 text-white" },
  completed: { label: "Completed", icon: CheckCircle2, className: "bg-green-500 text-white" },
  failed: { label: "Failed", icon: XCircle, className: "bg-red-500 text-white" },
};

const callTypeConfig = {
  inbound: { label: "Inbound", icon: PhoneIncoming, className: "text-green-500" },
  outbound: { label: "Outbound", icon: PhoneOutgoing, className: "text-blue-500" },
};

function formatDuration(seconds?: number): string {
  if (!seconds) return "--:--";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function CallList({ onCallSelect }: CallListProps) {
  const {
    calls,
    isLoadingCalls,
    callsError,
    setCalls,
    setLoadingCalls,
    setCallsError,
    callsFilter,
    setCallsFilter,
  } = useAdminStore();

  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 10;

  useEffect(() => {
    fetchCalls();
  }, [page]);

  const fetchCalls = async () => {
    setLoadingCalls(true);
    setCallsError(null);
    try {
      const [response, error] = await zoiceCallsAPI.getAll(page, pageSize);
      if (error) {
        setCallsError(error.message);
      } else if (response) {
        const mapped: ZoiceCall[] = response.data.map((c: ZoiceCallResponse) => ({
          id: c.id,
          pipeline_id: c.pipeline_id,
          call_type: c.call_type,
          status: c.status,
          from_number: c.from_number,
          to_number: c.to_number,
          duration_seconds: c.duration_seconds,
          transcript: c.transcript,
          recording_url: c.recording_url,
          created_at: c.created_at,
          ended_at: c.ended_at,
        }));
        setCalls(mapped);
        setTotalCount(response.total);
      }
    } catch (err) {
      setCallsError("Failed to fetch calls");
    } finally {
      setLoadingCalls(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchCalls();
    setRefreshing(false);
  };

  const columns: Column<ZoiceCall>[] = [
    {
      id: "call_type",
      header: "Type",
      accessorKey: "call_type",
      sortable: true,
      cell: (row) => {
        const config = callTypeConfig[row.call_type];
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
      id: "from_number",
      header: "From",
      accessorKey: "from_number",
      cell: (row) => (
        <span className="text-sm font-mono">{row.from_number}</span>
      ),
    },
    {
      id: "to_number",
      header: "To",
      accessorKey: "to_number",
      cell: (row) => (
        <span className="text-sm font-mono">{row.to_number}</span>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      sortable: true,
      cell: (row) => {
        const config = callStatusConfig[row.status];
        const Icon = config.icon;
        return (
          <Badge className={cn("text-xs gap-1", config.className)}>
            <Icon className="w-3 h-3" />
            {config.label}
          </Badge>
        );
      },
    },
    {
      id: "duration",
      header: "Duration",
      accessorKey: "duration_seconds",
      sortable: true,
      cell: (row) => (
        <div className="flex items-center gap-1 text-sm text-gray-500">
          <Clock className="w-3 h-3" />
          {formatDuration(row.duration_seconds)}
        </div>
      ),
    },
    {
      id: "has_transcript",
      header: "Transcript",
      cell: (row) => (
        <div className="flex items-center gap-1">
          {row.transcript ? (
            <Badge variant="outline" className="text-xs gap-1">
              <FileText className="w-3 h-3" />
              Available
            </Badge>
          ) : (
            <span className="text-xs text-gray-400">--</span>
          )}
        </div>
      ),
    },
    {
      id: "has_recording",
      header: "Recording",
      cell: (row) => (
        <div className="flex items-center gap-1">
          {row.recording_url ? (
            <Button variant="ghost" size="sm" className="h-7 px-2" onClick={(e) => e.stopPropagation()}>
              <Play className="w-3 h-3 mr-1" />
              Play
            </Button>
          ) : (
            <span className="text-xs text-gray-400">--</span>
          )}
        </div>
      ),
    },
    {
      id: "created_at",
      header: "Date",
      accessorKey: "created_at",
      sortable: true,
      cell: (row) => (
        <div className="text-sm">
          <p className="text-gray-900 dark:text-white">{format(new Date(row.created_at), "MMM d, yyyy")}</p>
          <p className="text-xs text-gray-500">{format(new Date(row.created_at), "h:mm a")}</p>
        </div>
      ),
    },
  ];

  // Stats cards
  const stats = {
    total: calls.length,
    completed: calls.filter((c) => c.status === "completed").length,
    failed: calls.filter((c) => c.status === "failed").length,
    avgDuration: calls.length > 0
      ? Math.round(calls.reduce((sum, c) => sum + (c.duration_seconds || 0), 0) / calls.length)
      : 0,
  };

  if (callsError) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full mb-4">
          <PhoneCall className="w-6 h-6 text-red-500" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Failed to load calls</h3>
        <p className="text-gray-500 dark:text-gray-400 mb-4">{callsError}</p>
        <Button onClick={handleRefresh} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Call History</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            View and manage voice AI call records
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={cn("w-4 h-4 mr-2", refreshing && "animate-spin")} />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Total Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{totalCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-500">{stats.completed}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Failed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-red-500">{stats.failed}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Avg Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{formatDuration(stats.avgDuration)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <DataTable
        data={calls}
        columns={columns}
        keyField="id"
        onRowClick={onCallSelect}
        isLoading={isLoadingCalls}
        searchPlaceholder="Search by phone number..."
        searchFields={["from_number", "to_number"]}
        statusTabs={[
          { value: null, label: "All" },
          { value: "completed", label: "Completed" },
          { value: "in_progress", label: "In Progress" },
          { value: "failed", label: "Failed" },
          { value: "queued", label: "Queued" },
        ]}
        totalCount={totalCount}
        currentPage={page}
        onPageChange={setPage}
        emptyMessage="No calls found"
      />
    </div>
  );
}

export default CallList;
