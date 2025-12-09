/**
 * WebSocket React Hook
 *
 * Provides real-time WebSocket functionality to React components.
 */

"use client";

import { createContext, useContext, useCallback, useEffect, useState, type Context } from 'react';
import type { MessageType, WebSocketMessage, Notification, ConnectionState } from '@/lib/websocket/types';
import type { WebSocketClient } from '@/lib/websocket';

// Context value type
export interface WebSocketContextValue {
  client: WebSocketClient | null;
  isConnected: boolean;
  connectionState: ConnectionState;
  send: (type: MessageType, payload: Record<string, unknown>) => Promise<void>;
  joinRoom: (roomId: string) => Promise<void>;
  leaveRoom: (roomId: string) => Promise<void>;
  subscribe: (topic: string) => Promise<void>;
  unsubscribe: (topic: string) => Promise<void>;
  sendMessage: (conversationId: string, content: string) => Promise<void>;
  startTyping: (conversationId: string) => void;
  stopTyping: (conversationId: string) => void;
  updatePresence: (status: 'online' | 'away' | 'busy' | 'offline', message?: string) => void;
}

// Create context here to avoid circular imports
export const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export interface UseWebSocketReturn {
  isConnected: boolean;
  connectionState: ConnectionState;
  send: (type: MessageType, payload: Record<string, unknown>) => Promise<void>;
  joinRoom: (roomId: string) => Promise<void>;
  leaveRoom: (roomId: string) => Promise<void>;
  subscribe: (topic: string) => Promise<void>;
  unsubscribe: (topic: string) => Promise<void>;
  sendMessage: (conversationId: string, content: string) => Promise<void>;
  startTyping: (conversationId: string) => void;
  stopTyping: (conversationId: string) => void;
  updatePresence: (status: 'online' | 'away' | 'busy' | 'offline', message?: string) => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const context = useContext(WebSocketContext);

  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }

  return context;
}

/**
 * Hook to subscribe to specific message types
 */
export function useWebSocketMessage(
  type: MessageType,
  handler: (message: WebSocketMessage) => void,
  deps: React.DependencyList = []
): void {
  const context = useContext(WebSocketContext);

  useEffect(() => {
    if (!context?.client) return;

    const cleanup = context.client.on(type, handler);
    return cleanup;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [context?.client, type, ...deps]);
}

/**
 * Hook to receive notifications
 */
export function useNotifications(): {
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (notificationId: string) => void;
  markAllAsRead: () => void;
  clearNotifications: () => void;
} {
  const context = useContext(WebSocketContext);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    if (!context?.client) return;

    const cleanup = context.client.on('notification', (message) => {
      const notification = message.payload as unknown as Notification;
      setNotifications(prev => [notification, ...prev].slice(0, 100));
    });

    return cleanup;
  }, [context?.client]);

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAsRead = useCallback((notificationId: string) => {
    setNotifications(prev =>
      prev.map(n =>
        n.notificationId === notificationId ? { ...n, read: true } : n
      )
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearNotifications,
  };
}

/**
 * Hook to track typing indicators
 */
export function useTypingIndicator(conversationId: string): {
  typingUsers: string[];
  startTyping: () => void;
  stopTyping: () => void;
} {
  const { startTyping: wsStartTyping, stopTyping: wsStopTyping } = useWebSocket();
  const context = useContext(WebSocketContext);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);

  useEffect(() => {
    if (!context?.client) return;

    const handleTypingStart = context.client.on('typing_start', (message) => {
      if (message.payload.conversationId === conversationId) {
        const userId = message.payload.userId as string;
        setTypingUsers(prev => prev.includes(userId) ? prev : [...prev, userId]);
      }
    });

    const handleTypingStop = context.client.on('typing_stop', (message) => {
      if (message.payload.conversationId === conversationId) {
        const userId = message.payload.userId as string;
        setTypingUsers(prev => prev.filter(id => id !== userId));
      }
    });

    return () => {
      handleTypingStart();
      handleTypingStop();
    };
  }, [context?.client, conversationId]);

  const startTyping = useCallback(() => {
    wsStartTyping(conversationId);
  }, [wsStartTyping, conversationId]);

  const stopTyping = useCallback(() => {
    wsStopTyping(conversationId);
  }, [wsStopTyping, conversationId]);

  return { typingUsers, startTyping, stopTyping };
}

/**
 * Hook to track presence of users
 */
export function usePresence(userIds: string[]): Map<string, { status: string; lastSeen?: string }> {
  const context = useContext(WebSocketContext);
  const [presence, setPresence] = useState<Map<string, { status: string; lastSeen?: string }>>(new Map());

  useEffect(() => {
    if (!context?.client) return;

    const cleanup = context.client.on('presence_update', (message) => {
      const userId = message.payload.userId as string;
      if (userIds.includes(userId)) {
        setPresence(prev => {
          const next = new Map(prev);
          next.set(userId, {
            status: message.payload.status as string,
            lastSeen: message.payload.lastSeen as string | undefined,
          });
          return next;
        });
      }
    });

    return cleanup;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [context?.client, userIds.join(',')]);

  return presence;
}

/**
 * Hook to subscribe to room messages
 */
export function useRoomMessages(roomId: string): {
  messages: WebSocketMessage[];
  sendMessage: (content: string) => Promise<void>;
  isLoading: boolean;
} {
  const { joinRoom, leaveRoom, sendMessage: wsSendMessage } = useWebSocket();
  const context = useContext(WebSocketContext);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!context?.client || !roomId) return;

    setIsLoading(true);
    joinRoom(roomId)
      .then(() => setIsLoading(false))
      .catch(() => setIsLoading(false));

    const cleanup = context.client.on('message', (message) => {
      if (message.payload.conversationId === roomId) {
        setMessages(prev => [...prev, message]);
      }
    });

    return () => {
      cleanup();
      leaveRoom(roomId);
    };
  }, [context?.client, roomId, joinRoom, leaveRoom]);

  const sendMessage = useCallback(async (content: string) => {
    await wsSendMessage(roomId, content);
  }, [wsSendMessage, roomId]);

  return { messages, sendMessage, isLoading };
}

/**
 * Hook to subscribe to events
 */
export function useEventSubscription(
  topic: string,
  handler: (data: Record<string, unknown>) => void,
  deps: React.DependencyList = []
): void {
  const { subscribe, unsubscribe } = useWebSocket();
  const context = useContext(WebSocketContext);

  useEffect(() => {
    if (!context?.client || !topic) return;

    subscribe(topic);

    const cleanup = context.client.on('event', (message) => {
      if (message.payload.topic === topic) {
        handler(message.payload.data as Record<string, unknown>);
      }
    });

    return () => {
      cleanup();
      unsubscribe(topic);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [context?.client, topic, subscribe, unsubscribe, ...deps]);
}
