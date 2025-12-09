/**
 * WebSocket Client Library
 *
 * Core WebSocket client that matches the backend FastAPI WebSocket infrastructure.
 * Handles connection management, authentication, reconnection, and message handling.
 */

// Re-export types
export type {
  MessageType,
  WebSocketMessage,
  Notification,
  ConnectionState,
} from './types';

import type {
  MessageType,
  WebSocketMessage,
  Notification,
  ConnectionState,
} from './types';

export interface WebSocketClientOptions {
  url: string;
  token?: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  onConnect?: () => void;
  onDisconnect?: (reason?: string) => void;
  onAuthenticated?: (userId: string, tenantId: string) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onNotification?: (notification: Notification) => void;
  onError?: (error: Error) => void;
  onStateChange?: (state: ConnectionState) => void;
}

interface ResolvedWebSocketClientOptions {
  url: string;
  token: string | undefined;
  reconnectAttempts: number;
  reconnectDelay: number;
  heartbeatInterval: number;
  onConnect: () => void;
  onDisconnect: (reason?: string) => void;
  onAuthenticated: (userId: string, tenantId: string) => void;
  onMessage: (message: WebSocketMessage) => void;
  onNotification: (notification: Notification) => void;
  onError: (error: Error) => void;
  onStateChange: (state: ConnectionState) => void;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private options: ResolvedWebSocketClientOptions;
  private state: ConnectionState = 'disconnected';
  private reconnectCount = 0;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Map<MessageType, Set<(message: WebSocketMessage) => void>> = new Map();
  private pendingAcks: Map<string, { resolve: (value: WebSocketMessage) => void; reject: (reason: Error) => void; timeout: NodeJS.Timeout }> = new Map();
  private subscriptions: Set<string> = new Set();
  private rooms: Set<string> = new Set();

  constructor(options: WebSocketClientOptions) {
    this.options = {
      token: undefined,
      reconnectAttempts: 5,
      reconnectDelay: 1000,
      heartbeatInterval: 30000,
      onConnect: () => {},
      onDisconnect: () => {},
      onAuthenticated: () => {},
      onMessage: () => {},
      onNotification: () => {},
      onError: () => {},
      onStateChange: () => {},
      ...options,
    };
  }

  get connectionState(): ConnectionState {
    return this.state;
  }

  get isConnected(): boolean {
    return this.state === 'connected' || this.state === 'authenticated';
  }

  connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.setState('connecting');

    const url = new URL(this.options.url);
    if (this.options.token) {
      url.searchParams.set('token', this.options.token);
    }

    try {
      this.ws = new WebSocket(url.toString());
      this.setupWebSocket();
    } catch (error) {
      this.handleError(error as Error);
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.clearTimers();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.setState('disconnected');
    this.options.onDisconnect('Client disconnect');
  }

  send(type: MessageType, payload: Record<string, unknown>, expectAck = false): Promise<WebSocketMessage | void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error('WebSocket not connected'));
    }

    const messageId = this.generateId();
    const message: WebSocketMessage = {
      type,
      payload,
      messageId,
      timestamp: new Date().toISOString(),
    };

    if (expectAck) {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          this.pendingAcks.delete(messageId);
          reject(new Error('Ack timeout'));
        }, 10000);

        this.pendingAcks.set(messageId, { resolve, reject, timeout });
        this.ws!.send(JSON.stringify(message));
      });
    }

    this.ws.send(JSON.stringify(message));
    return Promise.resolve();
  }

  authenticate(token: string): Promise<void> {
    return this.send('auth', { token }, true).then(() => {});
  }

  joinRoom(roomId: string): Promise<void> {
    return this.send('join_room', { roomId }, true).then(() => {
      this.rooms.add(roomId);
    });
  }

  leaveRoom(roomId: string): Promise<void> {
    return this.send('leave_room', { roomId }, true).then(() => {
      this.rooms.delete(roomId);
    });
  }

  subscribe(topic: string): Promise<void> {
    return this.send('subscribe', { topic }, true).then(() => {
      this.subscriptions.add(topic);
    });
  }

  unsubscribe(topic: string): Promise<void> {
    return this.send('unsubscribe', { topic }, true).then(() => {
      this.subscriptions.delete(topic);
    });
  }

  sendMessage(conversationId: string, content: string, contentType = 'text'): Promise<void> {
    return this.send('message', { conversationId, content, contentType }, true).then(() => {});
  }

  startTyping(conversationId: string): void {
    this.send('typing_start', { conversationId });
  }

  stopTyping(conversationId: string): void {
    this.send('typing_stop', { conversationId });
  }

  updatePresence(status: 'online' | 'away' | 'busy' | 'offline', statusMessage?: string): void {
    this.send('presence_update', { status, statusMessage });
  }

  on(type: MessageType, handler: (message: WebSocketMessage) => void): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);

    return () => {
      this.messageHandlers.get(type)?.delete(handler);
    };
  }

  off(type: MessageType, handler: (message: WebSocketMessage) => void): void {
    this.messageHandlers.get(type)?.delete(handler);
  }

  private setupWebSocket(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.reconnectCount = 0;
      this.setState('connected');
      this.options.onConnect();
      this.startHeartbeat();

      // Rejoin rooms and subscriptions after reconnect
      this.rooms.forEach(roomId => this.joinRoom(roomId));
      this.subscriptions.forEach(topic => this.subscribe(topic));
    };

    this.ws.onclose = (event) => {
      this.clearTimers();
      this.setState('disconnected');
      this.options.onDisconnect(event.reason);

      if (!event.wasClean) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (event) => {
      this.handleError(new Error('WebSocket error'));
    };

    this.ws.onmessage = (event) => {
      this.handleMessage(event.data);
    };
  }

  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data);

      // Handle system messages
      switch (message.type) {
        case 'connect':
          this.setState('connected');
          break;

        case 'auth_success':
          this.setState('authenticated');
          this.options.onAuthenticated(
            message.payload.userId as string,
            message.payload.tenantId as string
          );
          break;

        case 'auth_failure':
          this.handleError(new Error('Authentication failed'));
          break;

        case 'pong':
          // Heartbeat response received
          break;

        case 'ack':
          this.handleAck(message);
          break;

        case 'error':
          this.handleError(new Error(message.payload.error as string));
          break;

        case 'notification':
          this.options.onNotification(message.payload as unknown as Notification);
          break;

        default:
          this.options.onMessage(message);
      }

      // Call registered handlers
      const handlers = this.messageHandlers.get(message.type);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error('Message handler error:', error);
          }
        });
      }
    } catch (error) {
      console.error('Failed to parse message:', error);
    }
  }

  private handleAck(message: WebSocketMessage): void {
    const correlationId = message.correlationId;
    if (correlationId && this.pendingAcks.has(correlationId)) {
      const pending = this.pendingAcks.get(correlationId)!;
      clearTimeout(pending.timeout);
      pending.resolve(message);
      this.pendingAcks.delete(correlationId);
    }
  }

  private handleError(error: Error): void {
    console.error('WebSocket error:', error);
    this.options.onError(error);
  }

  private setState(state: ConnectionState): void {
    if (this.state !== state) {
      this.state = state;
      this.options.onStateChange(state);
    }
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send('ping', {});
      }
    }, this.options.heartbeatInterval);
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectCount >= this.options.reconnectAttempts) {
      this.options.onError(new Error('Max reconnect attempts reached'));
      return;
    }

    this.setState('reconnecting');
    const delay = this.options.reconnectDelay * Math.pow(2, this.reconnectCount);
    this.reconnectCount++;

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private clearTimers(): void {
    this.clearHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    // Clear all pending acks
    this.pendingAcks.forEach(pending => {
      clearTimeout(pending.timeout);
      pending.reject(new Error('Connection closed'));
    });
    this.pendingAcks.clear();
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

export function createWebSocketClient(options: WebSocketClientOptions): WebSocketClient {
  return new WebSocketClient(options);
}
