"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useCallback } from "react";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { WebSocketProvider } from "@/components/providers/websocket-provider";
import { ToastProvider, ToastViewport } from "@/components/ui/toast";
import type { Notification } from "@/lib/websocket/types";

export function Providers({ children }: { children: React.ReactNode }) {
  // Create a client with React 19 optimizations
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            gcTime: 10 * 60 * 1000, // 10 minutes (renamed from cacheTime in v5)
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  // WebSocket notification handler
  const handleNotification = useCallback((notification: Notification) => {
    // Invalidate relevant queries when notifications arrive
    if (notification.notificationType === 'appointment') {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
    } else if (notification.notificationType === 'message') {
      queryClient.invalidateQueries({ queryKey: ['messages'] });
    } else if (notification.notificationType === 'lab_result') {
      queryClient.invalidateQueries({ queryKey: ['lab-results'] });
    }
  }, [queryClient]);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="system" enableSystem>
        <WebSocketProvider
          url={process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/connect"}
          enabled={typeof window !== 'undefined'}
          onNotification={handleNotification}
        >
          <ToastProvider>
            {children}
            <ToastViewport />
          </ToastProvider>
        </WebSocketProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
