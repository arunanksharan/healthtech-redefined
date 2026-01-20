"use client";

import * as React from "react";
import { useEffect, useState } from "react";
import {
  Phone,
  Link as LinkIcon,
  Unlink,
  CheckCircle2,
  XCircle,
  MoreHorizontal,
  RefreshCw,
  Settings,
  Route,
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
import { useAdminStore, ZoicePhoneNumber } from "@/lib/store/admin-store";
import { zoicePhoneNumbersAPI, zoiceTelephonyAPI, ZoicePhoneNumberResponse } from "@/lib/api/zoice";
import { formatDistanceToNow } from "date-fns";

interface PhoneNumberListProps {
  onPhoneNumberSelect?: (phoneNumber: ZoicePhoneNumber) => void;
}

const statusConfig = {
  active: { label: "Active", icon: CheckCircle2, className: "bg-green-500 text-white" },
  inactive: { label: "Inactive", icon: XCircle, className: "bg-gray-400 text-white" },
};

export function PhoneNumberList({ onPhoneNumberSelect }: PhoneNumberListProps) {
  const {
    phoneNumbers,
    pipelines,
    isLoadingPhoneNumbers,
    phoneNumbersError,
    setPhoneNumbers,
    setLoadingPhoneNumbers,
    setPhoneNumbersError,
  } = useAdminStore();

  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchPhoneNumbers();
  }, []);

  const fetchPhoneNumbers = async () => {
    setLoadingPhoneNumbers(true);
    setPhoneNumbersError(null);
    try {
      // Fetch from telephony configs to get all phone numbers
      const [response, error] = await zoiceTelephonyAPI.getAll();
      if (error) {
        setPhoneNumbersError(error.message);
      } else if (response) {
        // Flatten phone numbers from all configs
        const allNumbers: ZoicePhoneNumber[] = [];
        for (const config of response) {
          for (const pn of config.phone_numbers) {
            allNumbers.push({
              id: pn.id,
              phone_number: pn.phone_number,
              provider: config.provider || pn.provider,
              status: pn.status,
              pipeline_id: pn.pipeline_id,
              created_at: pn.created_at,
            });
          }
        }
        setPhoneNumbers(allNumbers);
      }
    } catch (err) {
      setPhoneNumbersError("Failed to fetch phone numbers");
    } finally {
      setLoadingPhoneNumbers(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchPhoneNumbers();
    setRefreshing(false);
  };

  const getPipelineName = (pipelineId?: string) => {
    if (!pipelineId) return null;
    const pipeline = pipelines.find((p) => p.id === pipelineId);
    return pipeline?.name || "Unknown Pipeline";
  };

  const columns: Column<ZoicePhoneNumber>[] = [
    {
      id: "phone_number",
      header: "Phone Number",
      accessorKey: "phone_number",
      sortable: true,
      cell: (row) => (
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <Phone className="w-4 h-4 text-green-500" />
          </div>
          <span className="font-mono font-medium text-gray-900 dark:text-white">{row.phone_number}</span>
        </div>
      ),
    },
    {
      id: "provider",
      header: "Provider",
      accessorKey: "provider",
      sortable: true,
      cell: (row) => (
        <Badge variant="outline" className="text-xs capitalize">
          {row.provider}
        </Badge>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      sortable: true,
      cell: (row) => {
        const config = statusConfig[row.status];
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
      id: "pipeline",
      header: "Assigned Pipeline",
      cell: (row) => {
        const pipelineName = getPipelineName(row.pipeline_id);
        return pipelineName ? (
          <div className="flex items-center gap-2">
            <LinkIcon className="w-4 h-4 text-purple-500" />
            <span className="text-sm text-purple-600 dark:text-purple-400">{pipelineName}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-gray-400">
            <Unlink className="w-4 h-4" />
            <span className="text-sm">Unassigned</span>
          </div>
        );
      },
    },
    {
      id: "created_at",
      header: "Added",
      accessorKey: "created_at",
      sortable: true,
      cell: (row) => (
        <span className="text-sm text-gray-500">
          {formatDistanceToNow(new Date(row.created_at), { addSuffix: true })}
        </span>
      ),
    },
  ];

  // Stats
  const stats = {
    total: phoneNumbers.length,
    active: phoneNumbers.filter((p) => p.status === "active").length,
    assigned: phoneNumbers.filter((p) => p.pipeline_id).length,
    available: phoneNumbers.filter((p) => !p.pipeline_id && p.status === "active").length,
  };

  if (phoneNumbersError) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full mb-4">
          <Phone className="w-6 h-6 text-red-500" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Failed to load phone numbers</h3>
        <p className="text-gray-500 dark:text-gray-400 mb-4">{phoneNumbersError}</p>
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
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Phone Numbers</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Manage phone numbers for voice AI pipelines
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={cn("w-4 h-4 mr-2", refreshing && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Total Numbers</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-500">{stats.active}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Assigned</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <p className="text-2xl font-bold text-purple-500">{stats.assigned}</p>
              <Route className="w-5 h-5 text-purple-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Available</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-500">{stats.available}</p>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <DataTable
        data={phoneNumbers}
        columns={columns}
        keyField="id"
        onRowClick={onPhoneNumberSelect}
        isLoading={isLoadingPhoneNumbers}
        searchPlaceholder="Search phone numbers..."
        searchFields={["phone_number", "provider"]}
        statusTabs={[
          { value: null, label: "All", count: stats.total },
          { value: "active", label: "Active", count: stats.active },
          { value: "inactive", label: "Inactive", count: stats.total - stats.active },
        ]}
        emptyMessage="No phone numbers found"
      />
    </div>
  );
}

export default PhoneNumberList;
