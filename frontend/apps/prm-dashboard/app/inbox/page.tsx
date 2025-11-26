"use client";

import * as React from "react";
import { useState, useMemo, useCallback } from "react";
import {
  Filter,
  RefreshCw,
  CheckSquare,
  Inbox as InboxIcon,
  Bell,
  WifiOff,
  Wifi,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  FeedCard,
  FeedCardSkeleton,
  InboxContextPanel,
  FilterPanel,
  QuickFilterPills,
} from "@/components/inbox";
import { useInboxStore, selectFilteredItems, selectUnreadCount } from "@/lib/store/inbox-store";
import type { FeedItem, SuggestedAction } from "@/lib/store/inbox-store";

// Mock data for demonstration
const mockFeedItems: FeedItem[] = [
  {
    id: "1",
    channel: "zoice",
    timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 min ago
    patient: {
      id: "p1",
      name: "John Doe",
      phone: "+1 (555) 123-4567",
    },
    context: "Cardiology - Dr. Sharma",
    sentiment: {
      label: "frustrated",
      score: 87,
      emoji: "😤",
    },
    intent: "reschedule_appointment",
    preview: "I need to reschedule my appointment for tomorrow. The traffic is going to be terrible and I won't be able to make it on time...",
    priority: "high",
    status: "unread",
    suggestedActions: [
      { id: "a1", type: "reschedule", label: "Reschedule to Tue 2PM", isPrimary: true },
      { id: "a2", type: "reschedule", label: "Reschedule to Wed 3PM" },
      { id: "a3", type: "callback", label: "Callback Patient" },
    ],
    metadata: {
      callDuration: 272,
      recordingUrl: "https://example.com/recording.mp3",
    },
    isNew: true,
  },
  {
    id: "2",
    channel: "whatsapp",
    timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 min ago
    patient: {
      id: "p2",
      name: "Jane Smith",
      phone: "+1 (555) 234-5678",
    },
    context: "Insurance Verification",
    sentiment: {
      label: "positive",
      score: 92,
      emoji: "😊",
    },
    intent: "document_upload",
    preview: "Here's my insurance card for the upcoming appointment.",
    priority: "medium",
    status: "unread",
    attachments: [
      {
        id: "att1",
        type: "image",
        url: "https://example.com/insurance.jpg",
        name: "insurance_card.jpg",
        extractedData: {
          provider: "Aetna PPO",
          memberId: "XYZ123456",
        },
      },
    ],
    suggestedActions: [
      { id: "a4", type: "review", label: "Review Extraction", isPrimary: true },
      { id: "a5", type: "file", label: "File to Record" },
    ],
  },
  {
    id: "3",
    channel: "zoice",
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
    patient: {
      id: "p3",
      name: "Robert Wilson",
      phone: "+1 (555) 345-6789",
    },
    context: "General Medicine - Dr. Patel",
    sentiment: {
      label: "anxious",
      score: 78,
      emoji: "😰",
    },
    intent: "lab_results_inquiry",
    preview: "I've been waiting for my lab results for a week now. When will they be ready? I'm really worried about...",
    priority: "high",
    status: "pending",
    suggestedActions: [
      { id: "a6", type: "check_labs", label: "Check Lab Status", isPrimary: true },
      { id: "a7", type: "callback", label: "Callback Patient" },
    ],
    metadata: {
      callDuration: 185,
    },
  },
  {
    id: "4",
    channel: "email",
    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
    patient: {
      id: "p4",
      name: "Emily Brown",
      phone: "+1 (555) 456-7890",
    },
    context: "Orthopedics - Dr. Kumar",
    sentiment: {
      label: "neutral",
      score: 65,
      emoji: "😐",
    },
    intent: "appointment_confirmation",
    preview: "Confirming my appointment for next Monday at 10 AM with Dr. Kumar. Please let me know if there are any pre-visit instructions.",
    priority: "low",
    status: "read",
    suggestedActions: [
      { id: "a8", type: "confirm", label: "Send Confirmation", isPrimary: true },
      { id: "a9", type: "instructions", label: "Send Pre-Visit Info" },
    ],
  },
  {
    id: "5",
    channel: "sms",
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
    patient: {
      id: "p5",
      name: "Michael Davis",
      phone: "+1 (555) 567-8901",
    },
    context: "Dermatology - Dr. Singh",
    sentiment: {
      label: "positive",
      score: 88,
      emoji: "😊",
    },
    intent: "prescription_refill",
    preview: "Can you please refill my prescription for the skin cream? I'm running low.",
    priority: "medium",
    status: "resolved",
    suggestedActions: [
      { id: "a10", type: "refill", label: "Process Refill", isPrimary: true },
    ],
    resolvedBy: "Dr. Singh",
    resolvedAt: new Date(Date.now() - 12 * 60 * 60 * 1000),
  },
];

export default function InboxPage() {
  const {
    items,
    selectedItemId,
    filters,
    isConnected,
    isMultiSelectMode,
    selectedIds,
    isFilterPanelOpen,
    isLoading,
    setItems,
    selectItem,
    setFilters,
    resetFilters,
    toggleFilterPanel,
    toggleMultiSelect,
    toggleItemSelection,
    markAsRead,
    resolveItem,
    bulkAction,
    clearSelection,
    saveFilter,
  } = useInboxStore();

  // Initialize with mock data
  React.useEffect(() => {
    setItems(mockFeedItems);
  }, [setItems]);

  // Get filtered items
  const filteredItems = useMemo(() => {
    return selectFilteredItems({ items, filters } as any);
  }, [items, filters]);

  // Get unread count
  const unreadCount = useMemo(() => {
    return selectUnreadCount({ items } as any);
  }, [items]);

  // Get selected item
  const selectedItem = useMemo(() => {
    return items.find((item) => item.id === selectedItemId);
  }, [items, selectedItemId]);

  // Handlers
  const handleItemClick = useCallback((item: FeedItem) => {
    selectItem(item.id);
    if (item.status === "unread") {
      markAsRead([item.id]);
    }
  }, [selectItem, markAsRead]);

  const handleAction = useCallback((action: SuggestedAction) => {
    console.log("Action triggered:", action);
    // Would trigger actual action here
  }, []);

  const handleBulkAction = useCallback((action: "mark_read" | "mark_resolved" | "archive") => {
    bulkAction(action, Array.from(selectedIds));
  }, [bulkAction, selectedIds]);

  return (
    <div className="flex h-[calc(100vh-var(--topbar-height)-32px)] -m-4 lg:-m-6">
      {/* Main Feed */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="p-4 border-b border-border bg-card">
          {/* Title row */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold">Inbox</h1>
              {unreadCount > 0 && (
                <Badge variant="default">{unreadCount} unread</Badge>
              )}
              {/* Connection status */}
              <div className="flex items-center gap-1 text-xs">
                {isConnected ? (
                  <>
                    <Wifi className="h-3 w-3 text-success" />
                    <span className="text-success">Live</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="h-3 w-3 text-destructive" />
                    <span className="text-destructive">Offline</span>
                  </>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Button
                variant={isMultiSelectMode ? "default" : "outline"}
                size="sm"
                onClick={toggleMultiSelect}
              >
                <CheckSquare className="h-4 w-4 mr-2" />
                Select
              </Button>
              <Button
                variant={isFilterPanelOpen ? "default" : "outline"}
                size="sm"
                onClick={toggleFilterPanel}
              >
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
            </div>
          </div>

          {/* Quick filters */}
          <QuickFilterPills
            filters={filters}
            onFiltersChange={setFilters}
          />

          {/* Multi-select toolbar */}
          {isMultiSelectMode && selectedIds.size > 0 && (
            <div className="flex items-center gap-3 mt-4 p-3 bg-primary/5 rounded-lg">
              <span className="text-sm font-medium">{selectedIds.size} selected</span>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkAction("mark_read")}
                >
                  Mark as Read
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkAction("mark_resolved")}
                >
                  Resolve
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkAction("archive")}
                >
                  Archive
                </Button>
              </div>
              <Button size="sm" variant="ghost" onClick={clearSelection} className="ml-auto">
                Cancel
              </Button>
            </div>
          )}
        </div>

        {/* Feed content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {isLoading ? (
            // Loading state
            Array.from({ length: 5 }).map((_, i) => (
              <FeedCardSkeleton key={i} />
            ))
          ) : filteredItems.length === 0 ? (
            // Empty state
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <InboxIcon className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-1">All caught up!</h3>
              <p className="text-sm text-muted-foreground mb-4">
                No items match your current filters.
              </p>
              <Button variant="outline" onClick={resetFilters}>
                Clear Filters
              </Button>
            </div>
          ) : (
            // Feed items
            filteredItems.map((item) => (
              <FeedCard
                key={item.id}
                item={item}
                isSelected={selectedItemId === item.id}
                isMultiSelectMode={isMultiSelectMode}
                isChecked={selectedIds.has(item.id)}
                onClick={() => handleItemClick(item)}
                onCheck={() => toggleItemSelection(item.id)}
                onAction={handleAction}
                onMarkRead={() => markAsRead([item.id])}
                onMarkResolved={() => resolveItem(item.id, "current_user")}
              />
            ))
          )}
        </div>
      </div>

      {/* Context Panel */}
      {selectedItem && (
        <div className="w-96 border-l border-border hidden xl:block">
          <InboxContextPanel
            item={selectedItem}
            onClose={() => selectItem(null)}
            onAction={handleAction}
          />
        </div>
      )}

      {/* Filter Panel */}
      {isFilterPanelOpen && (
        <FilterPanel
          filters={filters}
          onFiltersChange={setFilters}
          onReset={resetFilters}
          onClose={toggleFilterPanel}
          onSaveFilter={saveFilter}
        />
      )}
    </div>
  );
}
