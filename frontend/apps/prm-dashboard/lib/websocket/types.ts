/**
 * WebSocket Types
 *
 * Shared types for WebSocket functionality
 */

export type MessageType =
  | 'ping'
  | 'pong'
  | 'connect'
  | 'disconnect'
  | 'error'
  | 'ack'
  | 'auth'
  | 'auth_success'
  | 'auth_failure'
  | 'presence_update'
  | 'typing_start'
  | 'typing_stop'
  | 'message'
  | 'message_delivered'
  | 'message_read'
  | 'join_room'
  | 'leave_room'
  | 'room_update'
  | 'notification'
  | 'event'
  | 'subscribe'
  | 'unsubscribe';

export interface WebSocketMessage {
  type: MessageType;
  payload: Record<string, unknown>;
  messageId: string;
  timestamp: string;
  correlationId?: string;
}

export interface Notification {
  notificationId: string;
  tenantId: string;
  recipientId: string;
  notificationType: string;
  title: string;
  body: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  data: Record<string, unknown>;
  actionUrl?: string;
  imageUrl?: string;
  createdAt: string;
  read: boolean;
}

export type ConnectionState =
  | 'connecting'
  | 'connected'
  | 'authenticated'
  | 'disconnected'
  | 'reconnecting';
