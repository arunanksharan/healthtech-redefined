import { create } from "zustand";
import { persist, devtools } from "zustand/middleware";

// Types for the inbox
export type ChannelType = "zoice" | "whatsapp" | "email" | "sms" | "app" | "system";
export type SentimentLabel = "positive" | "negative" | "neutral" | "frustrated" | "anxious";
export type PriorityLevel = "high" | "medium" | "low";
export type ItemStatus = "unread" | "read" | "pending" | "resolved" | "escalated";

export interface Patient {
  id: string;
  name: string;
  avatar?: string;
  phone?: string;
  email?: string;
}

export interface Sentiment {
  label: SentimentLabel;
  score: number; // 0-100
  emoji: string;
}

export interface Attachment {
  id: string;
  type: "image" | "document" | "audio" | "video";
  url: string;
  name: string;
  size?: number;
  thumbnail?: string;
  extractedData?: Record<string, string>;
}

export interface SuggestedAction {
  id: string;
  type: string;
  label: string;
  params?: Record<string, unknown>;
  isPrimary?: boolean;
}

export interface FeedItem {
  id: string;
  channel: ChannelType;
  timestamp: Date;
  patient: Patient;
  context: string; // Department, visit type, etc.
  sentiment: Sentiment;
  intent: string; // AI-detected intent
  preview: string; // Truncated message
  attachments?: Attachment[];
  priority: PriorityLevel;
  status: ItemStatus;
  suggestedActions: SuggestedAction[];
  metadata?: {
    callDuration?: number;
    recordingUrl?: string;
    transcriptId?: string;
    conversationId?: string;
    [key: string]: unknown;
  };
  isNew?: boolean;
  resolvedBy?: string;
  resolvedAt?: Date;
}

export interface InboxFilters {
  channels: ChannelType[];
  departments: string[];
  status: ItemStatus[];
  sentiments: SentimentLabel[];
  priorities: PriorityLevel[];
  dateRange: {
    from: Date | null;
    to: Date | null;
  };
  searchQuery: string;
  unreadOnly: boolean;
}

export interface SavedFilter {
  id: string;
  name: string;
  filters: InboxFilters;
  isDefault?: boolean;
}

export type BulkActionType = "mark_read" | "mark_resolved" | "archive" | "assign";

interface InboxState {
  // Data
  items: FeedItem[];
  selectedItemId: string | null;
  filters: InboxFilters;
  savedFilters: SavedFilter[];

  // Connection
  isConnected: boolean;
  lastSync: Date | null;
  reconnectAttempts: number;

  // UI State
  isMultiSelectMode: boolean;
  selectedIds: Set<string>;
  isFilterPanelOpen: boolean;
  isLoading: boolean;
  error: string | null;

  // Pagination
  cursor: string | null;
  hasMore: boolean;
  totalCount: number;
}

interface InboxActions {
  // Item operations
  setItems: (items: FeedItem[]) => void;
  addItem: (item: FeedItem) => void;
  updateItem: (id: string, updates: Partial<FeedItem>) => void;
  removeItem: (id: string) => void;
  prependItems: (items: FeedItem[]) => void;
  appendItems: (items: FeedItem[], cursor: string | null, hasMore: boolean) => void;

  // Selection
  selectItem: (id: string | null) => void;
  toggleMultiSelect: () => void;
  toggleItemSelection: (id: string) => void;
  selectAll: () => void;
  clearSelection: () => void;

  // Filters
  setFilters: (filters: Partial<InboxFilters>) => void;
  resetFilters: () => void;
  toggleFilterPanel: () => void;
  saveFilter: (name: string) => void;
  loadFilter: (filterId: string) => void;
  deleteFilter: (filterId: string) => void;

  // Actions
  markAsRead: (ids: string[]) => void;
  markAsUnread: (ids: string[]) => void;
  resolveItem: (id: string, resolvedBy: string) => void;
  bulkAction: (action: BulkActionType, ids: string[]) => void;

  // Connection
  setConnected: (connected: boolean) => void;
  setLastSync: (date: Date) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;

  // Loading & Error
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Reset
  reset: () => void;
}

const defaultFilters: InboxFilters = {
  channels: [],
  departments: [],
  status: [],
  sentiments: [],
  priorities: [],
  dateRange: {
    from: null,
    to: null,
  },
  searchQuery: "",
  unreadOnly: false,
};

const initialState: InboxState = {
  items: [],
  selectedItemId: null,
  filters: defaultFilters,
  savedFilters: [],
  isConnected: false,
  lastSync: null,
  reconnectAttempts: 0,
  isMultiSelectMode: false,
  selectedIds: new Set(),
  isFilterPanelOpen: false,
  isLoading: false,
  error: null,
  cursor: null,
  hasMore: true,
  totalCount: 0,
};

export const useInboxStore = create<InboxState & InboxActions>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // Item operations
        setItems: (items) => set({ items, cursor: null, hasMore: true }),

        addItem: (item) =>
          set((state) => ({
            items: [{ ...item, isNew: true }, ...state.items],
            totalCount: state.totalCount + 1,
          })),

        updateItem: (id, updates) =>
          set((state) => ({
            items: state.items.map((item) =>
              item.id === id ? { ...item, ...updates } : item
            ),
          })),

        removeItem: (id) =>
          set((state) => ({
            items: state.items.filter((item) => item.id !== id),
            selectedItemId: state.selectedItemId === id ? null : state.selectedItemId,
            totalCount: Math.max(0, state.totalCount - 1),
          })),

        prependItems: (items) =>
          set((state) => ({
            items: [...items.map((i) => ({ ...i, isNew: true })), ...state.items],
            totalCount: state.totalCount + items.length,
          })),

        appendItems: (items, cursor, hasMore) =>
          set((state) => ({
            items: [...state.items, ...items],
            cursor,
            hasMore,
          })),

        // Selection
        selectItem: (id) => set({ selectedItemId: id }),

        toggleMultiSelect: () =>
          set((state) => ({
            isMultiSelectMode: !state.isMultiSelectMode,
            selectedIds: state.isMultiSelectMode ? new Set() : state.selectedIds,
          })),

        toggleItemSelection: (id) =>
          set((state) => {
            const newSelected = new Set(state.selectedIds);
            if (newSelected.has(id)) {
              newSelected.delete(id);
            } else {
              newSelected.add(id);
            }
            return { selectedIds: newSelected };
          }),

        selectAll: () =>
          set((state) => ({
            selectedIds: new Set(state.items.map((item) => item.id)),
          })),

        clearSelection: () => set({ selectedIds: new Set(), isMultiSelectMode: false }),

        // Filters
        setFilters: (filters) =>
          set((state) => ({
            filters: { ...state.filters, ...filters },
          })),

        resetFilters: () => set({ filters: defaultFilters }),

        toggleFilterPanel: () =>
          set((state) => ({ isFilterPanelOpen: !state.isFilterPanelOpen })),

        saveFilter: (name) =>
          set((state) => ({
            savedFilters: [
              ...state.savedFilters,
              {
                id: `filter_${Date.now()}`,
                name,
                filters: { ...state.filters },
              },
            ],
          })),

        loadFilter: (filterId) =>
          set((state) => {
            const saved = state.savedFilters.find((f) => f.id === filterId);
            return saved ? { filters: saved.filters } : {};
          }),

        deleteFilter: (filterId) =>
          set((state) => ({
            savedFilters: state.savedFilters.filter((f) => f.id !== filterId),
          })),

        // Actions
        markAsRead: (ids) =>
          set((state) => ({
            items: state.items.map((item) =>
              ids.includes(item.id) ? { ...item, status: "read" as ItemStatus, isNew: false } : item
            ),
          })),

        markAsUnread: (ids) =>
          set((state) => ({
            items: state.items.map((item) =>
              ids.includes(item.id) ? { ...item, status: "unread" as ItemStatus } : item
            ),
          })),

        resolveItem: (id, resolvedBy) =>
          set((state) => ({
            items: state.items.map((item) =>
              item.id === id
                ? {
                    ...item,
                    status: "resolved" as ItemStatus,
                    resolvedBy,
                    resolvedAt: new Date(),
                  }
                : item
            ),
          })),

        bulkAction: (action, ids) => {
          const state = get();
          switch (action) {
            case "mark_read":
              state.markAsRead(ids);
              break;
            case "mark_resolved":
              ids.forEach((id) => state.resolveItem(id, "current_user"));
              break;
            case "archive":
              ids.forEach((id) => state.removeItem(id));
              break;
            default:
              break;
          }
          set({ selectedIds: new Set(), isMultiSelectMode: false });
        },

        // Connection
        setConnected: (connected) => set({ isConnected: connected }),
        setLastSync: (date) => set({ lastSync: date }),
        incrementReconnectAttempts: () =>
          set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 })),
        resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),

        // Loading & Error
        setLoading: (loading) => set({ isLoading: loading }),
        setError: (error) => set({ error }),

        // Reset
        reset: () => set(initialState),
      }),
      {
        name: "inbox-storage",
        partialize: (state) => ({
          filters: state.filters,
          savedFilters: state.savedFilters,
        }),
      }
    ),
    { name: "inbox-store" }
  )
);

// Selectors
export const selectFilteredItems = (state: InboxState): FeedItem[] => {
  let items = state.items;

  const { filters } = state;

  // Filter by channels
  if (filters.channels.length > 0) {
    items = items.filter((item) => filters.channels.includes(item.channel));
  }

  // Filter by status
  if (filters.status.length > 0) {
    items = items.filter((item) => filters.status.includes(item.status));
  }

  // Filter by sentiments
  if (filters.sentiments.length > 0) {
    items = items.filter((item) => filters.sentiments.includes(item.sentiment.label));
  }

  // Filter by priorities
  if (filters.priorities.length > 0) {
    items = items.filter((item) => filters.priorities.includes(item.priority));
  }

  // Filter by unread only
  if (filters.unreadOnly) {
    items = items.filter((item) => item.status === "unread");
  }

  // Filter by search query
  if (filters.searchQuery) {
    const query = filters.searchQuery.toLowerCase();
    items = items.filter(
      (item) =>
        item.patient.name.toLowerCase().includes(query) ||
        item.preview.toLowerCase().includes(query) ||
        item.intent.toLowerCase().includes(query)
    );
  }

  // Filter by date range
  if (filters.dateRange.from) {
    items = items.filter((item) => new Date(item.timestamp) >= filters.dateRange.from!);
  }
  if (filters.dateRange.to) {
    items = items.filter((item) => new Date(item.timestamp) <= filters.dateRange.to!);
  }

  return items;
};

export const selectUnreadCount = (state: InboxState): number => {
  return state.items.filter((item) => item.status === "unread").length;
};

export const selectHighPriorityCount = (state: InboxState): number => {
  return state.items.filter((item) => item.priority === "high" && item.status !== "resolved").length;
};

export default useInboxStore;
