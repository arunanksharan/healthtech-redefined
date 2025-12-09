"use client";

/**
 * WebSocket Provider
 *
 * Manages WebSocket connection lifecycle and provides context to child components.
 */

import React, { useEffect, useMemo, useState } from "react";
import {
  WebSocketClient,
  createWebSocketClient,
} from "@/lib/websocket";
import type {
  ConnectionState,
  MessageType,
  Notification,
} from "@/lib/websocket/types";
import { WebSocketContext } from "@/lib/hooks/useWebSocket";

interface WebSocketProviderProps {
  children: React.ReactNode;
  url?: string;
  token?: string;
  enabled?: boolean;
  onConnect?: () => void;
  onDisconnect?: (reason?: string) => void;
  onNotification?: (notification: Notification) => void;
  onError?: (error: Error) => void;
}

export function WebSocketProvider({
  children,
  url = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/connect",
  token,
  enabled = true,
  onConnect,
  onDisconnect,
  onNotification,
  onError,
}: WebSocketProviderProps) {
  const [client, setClient] = useState<WebSocketClient | null>(null);
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");

  // Initialize WebSocket client
  useEffect(() => {
    if (!enabled || typeof window === "undefined") {
      return;
    }

    const wsClient = createWebSocketClient({
      url,
      token,
      reconnectAttempts: 5,
      reconnectDelay: 1000,
      heartbeatInterval: 30000,
      onConnect: () => {
        onConnect?.();
      },
      onDisconnect: (reason) => {
        onDisconnect?.(reason);
      },
      onAuthenticated: (userId, tenantId) => {
        console.log(`WebSocket authenticated: ${userId}@${tenantId}`);
      },
      onNotification: (notification) => {
        onNotification?.(notification);
      },
      onError: (error) => {
        console.error("WebSocket error:", error);
        onError?.(error);
      },
      onStateChange: setConnectionState,
    });

    setClient(wsClient);
    wsClient.connect();

    return () => {
      wsClient.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, token, enabled]);

  // Memoized context value
  const contextValue = useMemo(() => {
    const send = async (
      type: MessageType,
      payload: Record<string, unknown>
    ): Promise<void> => {
      if (!client) {
        console.warn("WebSocket not connected");
        return;
      }
      await client.send(type, payload);
    };

    const joinRoom = async (roomId: string): Promise<void> => {
      if (!client) return;
      await client.joinRoom(roomId);
    };

    const leaveRoom = async (roomId: string): Promise<void> => {
      if (!client) return;
      await client.leaveRoom(roomId);
    };

    const subscribe = async (topic: string): Promise<void> => {
      if (!client) return;
      await client.subscribe(topic);
    };

    const unsubscribe = async (topic: string): Promise<void> => {
      if (!client) return;
      await client.unsubscribe(topic);
    };

    const sendMessage = async (
      conversationId: string,
      content: string
    ): Promise<void> => {
      if (!client) return;
      await client.sendMessage(conversationId, content);
    };

    const startTyping = (conversationId: string): void => {
      client?.startTyping(conversationId);
    };

    const stopTyping = (conversationId: string): void => {
      client?.stopTyping(conversationId);
    };

    const updatePresence = (
      status: "online" | "away" | "busy" | "offline",
      message?: string
    ): void => {
      client?.updatePresence(status, message);
    };

    return {
      client,
      isConnected: connectionState === "connected" || connectionState === "authenticated",
      connectionState,
      send,
      joinRoom,
      leaveRoom,
      subscribe,
      unsubscribe,
      sendMessage,
      startTyping,
      stopTyping,
      updatePresence,
    };
  }, [client, connectionState]);

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

// Re-export context for convenience
export { WebSocketContext } from "@/lib/hooks/useWebSocket";
