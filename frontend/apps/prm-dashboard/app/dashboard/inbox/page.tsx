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
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from "@/components/ui/resizable";
import { ScrollArea } from "@/components/ui/scroll-area";
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
        // FIX 1: Main container set to fixed height with flex-col. 
        // Uses h-[calc(100vh-6rem)] to account for navbar/margins.
        <div className="flex flex-col h-[calc(100vh-6rem)] overflow-hidden border border-gray-200 rounded-xl shadow-sm bg-white">

            <ResizablePanelGroup direction="horizontal" className="h-full">

                {/* Left Panel: Feed List */}
                <ResizablePanel
                    defaultSize={40}
                    minSize={30}
                    maxSize={50}
                    className="bg-white border-r border-gray-200 flex flex-col h-full"
                >
                    {/* FIX 2: Sticky Header. 
              Removed 'sticky' class. Because this is a flex column, this div will naturally stay at the top.
              'shrink-0' ensures it doesn't get squashed. */}
                    <div className="p-4 border-b border-gray-200 bg-white shrink-0 z-10">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <h1 className="text-xl font-bold text-gray-900">Inbox</h1>
                                {unreadCount > 0 && (
                                    <Badge variant="default" className="bg-blue-600 hover:bg-blue-700">
                                        {unreadCount} unread
                                    </Badge>
                                )}
                                <div className="flex items-center gap-1 text-xs">
                                    {isConnected ? (
                                        <>
                                            <Wifi className="h-3 w-3 text-green-500" />
                                            <span className="text-green-600 font-medium">Live</span>
                                        </>
                                    ) : (
                                        <>
                                            <WifiOff className="h-3 w-3 text-red-500" />
                                            <span className="text-red-500">Offline</span>
                                        </>
                                    )}
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500">
                                    <RefreshCw className="h-4 w-4" />
                                </Button>
                                <Button
                                    variant={isMultiSelectMode ? "secondary" : "ghost"}
                                    size="icon"
                                    className={cn("h-8 w-8", isMultiSelectMode ? "text-blue-600 bg-blue-50" : "text-gray-500")}
                                    onClick={toggleMultiSelect}
                                >
                                    <CheckSquare className="h-4 w-4" />
                                </Button>
                                <Button
                                    variant={isFilterPanelOpen ? "secondary" : "ghost"}
                                    size="icon"
                                    className={cn("h-8 w-8", isFilterPanelOpen ? "text-blue-600 bg-blue-50" : "text-gray-500")}
                                    onClick={toggleFilterPanel}
                                >
                                    <Filter className="h-4 w-4" />
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
                            <div className="flex items-center justify-between mt-3 p-2 bg-blue-50/50 rounded-lg border border-blue-100">
                                <span className="text-sm font-medium text-blue-900">{selectedIds.size} selected</span>
                                <div className="flex items-center gap-1">
                                    <Button size="sm" variant="ghost" onClick={() => handleBulkAction("mark_read")} className="h-7 text-blue-700 hover:bg-blue-100/50">Read</Button>
                                    <Button size="sm" variant="ghost" onClick={() => handleBulkAction("mark_resolved")} className="h-7 text-blue-700 hover:bg-blue-100/50">Resolve</Button>
                                    <Button size="sm" variant="ghost" onClick={() => handleBulkAction("archive")} className="h-7 text-blue-700 hover:bg-blue-100/50">Archive</Button>
                                    <Button size="sm" variant="ghost" onClick={clearSelection} className="h-7 text-gray-500 hover:bg-gray-100">Cancel</Button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* FIX 2 Continued: Scrollable Feed Content.
              'flex-1' makes it take up all remaining space. 
              The ScrollArea handles the internal scrolling. */}
                    <ScrollArea className="flex-1">
                        <div className="p-4 space-y-3">
                            {isLoading ? (
                                Array.from({ length: 5 }).map((_, i) => (
                                    <FeedCardSkeleton key={i} />
                                ))
                            ) : filteredItems.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 text-center">
                                    <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                                        <InboxIcon className="h-8 w-8 text-gray-300" />
                                    </div>
                                    <h3 className="text-lg font-medium text-gray-900 mb-1">All caught up!</h3>
                                    <p className="text-sm text-gray-500 mb-4 max-w-xs mx-auto">
                                        No items match your current filters. Check back later for new messages.
                                    </p>
                                    <Button variant="outline" onClick={resetFilters} className="border-gray-200 text-gray-600">
                                        Clear Filters
                                    </Button>
                                </div>
                            ) : (
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
                    </ScrollArea>
                </ResizablePanel>

                <ResizableHandle />

                {/* Right Panel: Context / Details */}
                <ResizablePanel defaultSize={60} className="h-full">
                    {selectedItem ? (
                        // FIX 3: Wrapped content in ScrollArea. 
                        // This ensures long content (like attachments) scrolls INSIDE the panel
                        // instead of stretching the page.
                        <ScrollArea className="h-full">
                            <InboxContextPanel
                                item={selectedItem}
                                onClose={() => selectItem(null)}
                                onAction={handleAction}
                            />
                        </ScrollArea>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center bg-gray-50/50 text-center p-8">
                            <div className="w-24 h-24 bg-white rounded-2xl shadow-sm border border-gray-100 flex items-center justify-center mb-6">
                                <InboxIcon className="h-10 w-10 text-gray-300" />
                            </div>
                            <h2 className="text-xl font-semibold text-gray-900 mb-2">Select a conversation</h2>
                            <p className="text-gray-500 max-w-sm">
                                Choose an item from the list to view details, patient context, and suggested actions.
                            </p>
                        </div>
                    )}
                </ResizablePanel>
            </ResizablePanelGroup>

            {/* Filter Panel Drawer/Dialog (kept as overlay) */}
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
