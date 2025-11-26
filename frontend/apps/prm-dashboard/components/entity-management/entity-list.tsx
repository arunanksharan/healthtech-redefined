"use client";

import * as React from "react";
import {
  Search,
  Filter,
  SortAsc,
  SortDesc,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  CheckSquare,
  Square,
  Loader2,
  Download,
  Upload,
  Plus,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ============================================================================
// Types
// ============================================================================

export interface ColumnDef<T> {
  id: string;
  header: string;
  accessor: keyof T | ((row: T) => React.ReactNode);
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
  align?: "left" | "center" | "right";
  render?: (value: unknown, row: T) => React.ReactNode;
}

export interface FilterConfig {
  id: string;
  label: string;
  type: "select" | "multi-select" | "date-range" | "search";
  options?: { value: string; label: string }[];
  placeholder?: string;
}

export interface SortOption {
  id: string;
  label: string;
  field: string;
}

export interface PaginationConfig {
  page: number;
  pageSize: number;
  total: number;
  pageSizeOptions?: number[];
}

export interface EntityListProps<T extends { id: string }> {
  title: string;
  description?: string;
  data: T[];
  columns: ColumnDef<T>[];
  filters?: FilterConfig[];
  sortOptions?: SortOption[];
  searchPlaceholder?: string;
  onRowClick?: (row: T) => void;
  onBulkAction?: (action: string, rows: T[]) => void;
  pagination?: PaginationConfig;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  onSearch?: (search: string) => void;
  onFilter?: (filterId: string, value: string) => void;
  onSort?: (sortId: string, direction: "asc" | "desc") => void;
  isLoading?: boolean;
  onRefresh?: () => void;
  onAdd?: () => void;
  onImport?: () => void;
  onExport?: () => void;
  bulkActions?: { id: string; label: string; icon?: React.ComponentType<{ className?: string }> }[];
  emptyState?: React.ReactNode;
  className?: string;
}

// ============================================================================
// Entity List Component
// ============================================================================

export function EntityList<T extends { id: string }>({
  title,
  description,
  data,
  columns,
  filters = [],
  sortOptions = [],
  searchPlaceholder = "Search...",
  onRowClick,
  onBulkAction,
  pagination,
  onPageChange,
  onPageSizeChange,
  onSearch,
  onFilter,
  onSort,
  isLoading = false,
  onRefresh,
  onAdd,
  onImport,
  onExport,
  bulkActions = [],
  emptyState,
  className,
}: EntityListProps<T>) {
  const [searchValue, setSearchValue] = React.useState("");
  const [selectedRows, setSelectedRows] = React.useState<Set<string>>(new Set());
  const [sortConfig, setSortConfig] = React.useState<{ field: string; direction: "asc" | "desc" } | null>(null);
  const [filterValues, setFilterValues] = React.useState<Record<string, string>>({});

  // Select all toggle
  const allSelected = data.length > 0 && selectedRows.size === data.length;
  const someSelected = selectedRows.size > 0 && selectedRows.size < data.length;

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(data.map((row) => row.id)));
    }
  };

  const toggleSelectRow = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newSelected = new Set(selectedRows);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedRows(newSelected);
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
    onSearch?.(e.target.value);
  };

  const handleSort = (field: string) => {
    const newDirection = sortConfig?.field === field && sortConfig.direction === "asc" ? "desc" : "asc";
    setSortConfig({ field, direction: newDirection });
    onSort?.(field, newDirection);
  };

  const handleFilter = (filterId: string, value: string) => {
    setFilterValues((prev) => ({ ...prev, [filterId]: value }));
    onFilter?.(filterId, value);
  };

  const handleBulkAction = (action: string) => {
    const selectedData = data.filter((row) => selectedRows.has(row.id));
    onBulkAction?.(action, selectedData);
    setSelectedRows(new Set());
  };

  const getCellValue = (row: T, column: ColumnDef<T>): React.ReactNode => {
    const value = typeof column.accessor === "function"
      ? column.accessor(row)
      : row[column.accessor];

    if (column.render) {
      return column.render(value, row);
    }

    return value as React.ReactNode;
  };

  const totalPages = pagination ? Math.ceil(pagination.total / pagination.pageSize) : 1;

  return (
    <Card className={className}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">{title}</h2>
            {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
          </div>

          <div className="flex items-center gap-2">
            {onRefresh && (
              <Button variant="outline" size="icon" onClick={onRefresh} disabled={isLoading}>
                <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
              </Button>
            )}
            {onExport && (
              <Button variant="outline" size="sm" onClick={onExport}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            )}
            {onImport && (
              <Button variant="outline" size="sm" onClick={onImport}>
                <Upload className="h-4 w-4 mr-2" />
                Import
              </Button>
            )}
            {onAdd && (
              <Button size="sm" onClick={onAdd}>
                <Plus className="h-4 w-4 mr-2" />
                Add New
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Search and Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={searchValue}
              onChange={handleSearch}
              placeholder={searchPlaceholder}
              className="w-full pl-10 pr-4 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {/* Filters */}
          {filters.map((filter) => (
            <Select
              key={filter.id}
              value={filterValues[filter.id] || "all"}
              onValueChange={(value) => handleFilter(filter.id, value)}
            >
              <SelectTrigger className="w-[180px] h-9">
                <SelectValue placeholder={filter.label} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All {filter.label}</SelectItem>
                {filter.options?.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ))}

          {/* Sort */}
          {sortOptions.length > 0 && (
            <Select
              value={sortConfig?.field || ""}
              onValueChange={(value) => handleSort(value)}
            >
              <SelectTrigger className="w-[150px] h-9">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                {sortOptions.map((option) => (
                  <SelectItem key={option.id} value={option.field}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* Bulk Actions (shown when items selected) */}
        {selectedRows.size > 0 && bulkActions.length > 0 && (
          <div className="flex items-center gap-2 p-2 bg-primary/5 rounded-lg">
            <span className="text-sm font-medium">
              {selectedRows.size} selected
            </span>
            <div className="flex-1" />
            {bulkActions.map((action) => (
              <Button
                key={action.id}
                variant="outline"
                size="sm"
                onClick={() => handleBulkAction(action.id)}
              >
                {action.icon && <action.icon className="h-4 w-4 mr-2" />}
                {action.label}
              </Button>
            ))}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedRows(new Set())}
            >
              Clear
            </Button>
          </div>
        )}

        {/* Table */}
        <div className="border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  {/* Checkbox column */}
                  {bulkActions.length > 0 && (
                    <th className="w-10 p-3 text-left">
                      <button
                        onClick={toggleSelectAll}
                        className="flex items-center justify-center"
                      >
                        {allSelected ? (
                          <CheckSquare className="h-4 w-4 text-primary" />
                        ) : someSelected ? (
                          <CheckSquare className="h-4 w-4 text-primary/50" />
                        ) : (
                          <Square className="h-4 w-4 text-muted-foreground" />
                        )}
                      </button>
                    </th>
                  )}

                  {/* Data columns */}
                  {columns.map((column) => (
                    <th
                      key={column.id}
                      className={cn(
                        "p-3 text-xs font-medium text-muted-foreground uppercase tracking-wider",
                        column.align === "center" && "text-center",
                        column.align === "right" && "text-right",
                        column.sortable && "cursor-pointer hover:text-foreground"
                      )}
                      style={{ width: column.width }}
                      onClick={() => column.sortable && handleSort(column.id)}
                    >
                      <div className="flex items-center gap-1">
                        {column.header}
                        {column.sortable && sortConfig?.field === column.id && (
                          sortConfig.direction === "asc" ? (
                            <SortAsc className="h-3 w-3" />
                          ) : (
                            <SortDesc className="h-3 w-3" />
                          )
                        )}
                      </div>
                    </th>
                  ))}

                  {/* Actions column */}
                  <th className="w-10 p-3" />
                </tr>
              </thead>

              <tbody>
                {isLoading ? (
                  <tr>
                    <td
                      colSpan={columns.length + (bulkActions.length > 0 ? 2 : 1)}
                      className="p-8 text-center"
                    >
                      <div className="flex flex-col items-center gap-2">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <span className="text-sm text-muted-foreground">Loading...</span>
                      </div>
                    </td>
                  </tr>
                ) : data.length === 0 ? (
                  <tr>
                    <td
                      colSpan={columns.length + (bulkActions.length > 0 ? 2 : 1)}
                      className="p-8 text-center"
                    >
                      {emptyState || (
                        <div className="flex flex-col items-center gap-2">
                          <Search className="h-8 w-8 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">No data found</span>
                        </div>
                      )}
                    </td>
                  </tr>
                ) : (
                  data.map((row) => (
                    <tr
                      key={row.id}
                      className={cn(
                        "border-t hover:bg-muted/50 transition-colors",
                        onRowClick && "cursor-pointer",
                        selectedRows.has(row.id) && "bg-primary/5"
                      )}
                      onClick={() => onRowClick?.(row)}
                    >
                      {/* Checkbox */}
                      {bulkActions.length > 0 && (
                        <td className="p-3">
                          <button
                            onClick={(e) => toggleSelectRow(row.id, e)}
                            className="flex items-center justify-center"
                          >
                            {selectedRows.has(row.id) ? (
                              <CheckSquare className="h-4 w-4 text-primary" />
                            ) : (
                              <Square className="h-4 w-4 text-muted-foreground" />
                            )}
                          </button>
                        </td>
                      )}

                      {/* Data cells */}
                      {columns.map((column) => (
                        <td
                          key={column.id}
                          className={cn(
                            "p-3 text-sm",
                            column.align === "center" && "text-center",
                            column.align === "right" && "text-right"
                          )}
                        >
                          {getCellValue(row, column)}
                        </td>
                      ))}

                      {/* Row actions */}
                      <td className="p-3">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => onRowClick?.(row)}>
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem>Edit</DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-destructive">
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        {pagination && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                Showing {((pagination.page - 1) * pagination.pageSize) + 1} to{" "}
                {Math.min(pagination.page * pagination.pageSize, pagination.total)} of{" "}
                {pagination.total}
              </span>

              {onPageSizeChange && pagination.pageSizeOptions && (
                <Select
                  value={pagination.pageSize.toString()}
                  onValueChange={(value) => onPageSizeChange(parseInt(value))}
                >
                  <SelectTrigger className="w-[100px] h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {pagination.pageSizeOptions.map((size) => (
                      <SelectItem key={size} value={size.toString()}>
                        {size} per page
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => onPageChange?.(pagination.page - 1)}
                disabled={pagination.page <= 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>

              {/* Page numbers */}
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = pagination.page <= 3
                  ? i + 1
                  : pagination.page >= totalPages - 2
                    ? totalPages - 4 + i
                    : pagination.page - 2 + i;

                if (pageNum < 1 || pageNum > totalPages) return null;

                return (
                  <Button
                    key={pageNum}
                    variant={pagination.page === pageNum ? "default" : "outline"}
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => onPageChange?.(pageNum)}
                  >
                    {pageNum}
                  </Button>
                );
              })}

              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => onPageChange?.(pagination.page + 1)}
                disabled={pagination.page >= totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Status Badge Component (commonly used)
// ============================================================================

interface StatusBadgeProps {
  status: string;
  variant?: "default" | "success" | "warning" | "destructive" | "secondary";
}

export function StatusBadge({ status, variant }: StatusBadgeProps) {
  const getVariant = () => {
    if (variant) return variant;

    switch (status.toLowerCase()) {
      case "active":
      case "completed":
      case "fulfilled":
        return "success" as const;
      case "pending":
      case "on_leave":
      case "busy":
        return "warning" as const;
      case "inactive":
      case "suspended":
      case "cancelled":
        return "destructive" as const;
      default:
        return "secondary" as const;
    }
  };

  return (
    <Badge variant={getVariant()} className="capitalize">
      {status.replace(/_/g, " ")}
    </Badge>
  );
}

export default EntityList;
