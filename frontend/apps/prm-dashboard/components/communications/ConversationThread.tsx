'use client';

import React, { useState, useEffect, useRef } from 'react';
import { format, formatDistanceToNow } from 'date-fns';
import {
  MessageCircle,
  Phone,
  Mail,
  Send,
  Paperclip,
  Image as ImageIcon,
  FileText,
  Volume2,
  Download,
  ThumbsUp,
  ThumbsDown,
  Meh,
  Search,
  Filter,
} from 'lucide-react';

// ==================== Types ====================

interface Message {
  id: string;
  conversationId: string;
  direction: 'inbound' | 'outbound';
  actorType: 'patient' | 'agent' | 'bot' | 'system';
  contentType: 'text' | 'media' | 'voice' | 'file';
  textBody?: string;
  mediaUrl?: string;
  mediaType?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  intent?: string;
  createdAt: string;
  deliveryStatus?: 'queued' | 'sending' | 'sent' | 'delivered' | 'failed' | 'read';
}

interface Conversation {
  id: string;
  patientId?: string;
  patientName?: string;
  subject?: string;
  status: 'open' | 'pending' | 'snoozed' | 'closed';
  priority: 'p0' | 'p1' | 'p2' | 'p3';
  channelType: 'whatsapp' | 'sms' | 'email' | 'phone' | 'webchat';
  lastMessageAt?: string;
  messageCount: number;
}

interface ConversationThreadProps {
  conversation: Conversation;
  onSendMessage?: (message: string) => void;
  onClose?: () => void;
}

// ==================== Helper Components ====================

const ChannelIcon = ({ channel }: { channel: string }) => {
  switch (channel) {
    case 'whatsapp':
      return <MessageCircle className="w-4 h-4 text-green-600" />;
    case 'phone':
      return <Phone className="w-4 h-4 text-blue-600" />;
    case 'email':
      return <Mail className="w-4 h-4 text-purple-600 dark:text-purple-400" />;
    case 'sms':
      return <MessageCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />;
    default:
      return <MessageCircle className="w-4 h-4 text-muted-foreground" />;
  }
};

const SentimentIcon = ({ sentiment }: { sentiment?: string }) => {
  if (!sentiment) return null;

  switch (sentiment) {
    case 'positive':
      return <ThumbsUp className="w-3 h-3 text-green-600" />;
    case 'negative':
      return <ThumbsDown className="w-3 h-3 text-red-600" />;
    case 'neutral':
      return <Meh className="w-3 h-3 text-gray-600" />;
    default:
      return null;
  }
};

const MessageBubble = ({ message }: { message: Message }) => {
  const isInbound = message.direction === 'inbound';
  const isSystem = message.actorType === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <div className="bg-muted text-muted-foreground text-xs px-4 py-2 rounded-full">
          {message.textBody}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isInbound ? 'justify-start' : 'justify-end'} mb-4`}>
      <div
        className={`max-w-[70%] rounded-lg px-4 py-2 ${isInbound
            ? 'bg-card border border-border'
            : 'bg-blue-600 text-white'
          }`}
      >
        {/* Message Content */}
        {message.contentType === 'text' && (
          <p className="text-sm whitespace-pre-wrap">{message.textBody}</p>
        )}

        {message.contentType === 'media' && message.mediaUrl && (
          <div className="space-y-2">
            {message.mediaType?.startsWith('image/') && (
              <img
                src={message.mediaUrl}
                alt="Attachment"
                className="rounded-lg max-w-full"
              />
            )}
            {message.mediaType?.startsWith('video/') && (
              <video
                src={message.mediaUrl}
                controls
                className="rounded-lg max-w-full"
              />
            )}
            {message.textBody && (
              <p className="text-sm">{message.textBody}</p>
            )}
          </div>
        )}

        {message.contentType === 'voice' && message.mediaUrl && (
          <div className="flex items-center space-x-2">
            <Volume2 className="w-4 h-4" />
            <audio src={message.mediaUrl} controls className="flex-1" />
          </div>
        )}

        {message.contentType === 'file' && message.mediaUrl && (
          <a
            href={message.mediaUrl}
            download
            className="flex items-center space-x-2 hover:underline"
          >
            <FileText className="w-4 h-4" />
            <span className="text-sm">Download File</span>
            <Download className="w-3 h-3" />
          </a>
        )}

        {/* Message Metadata */}
        className={`flex items-center justify-between mt-2 text-xs ${isInbound ? 'text-muted-foreground' : 'text-blue-100'
          }`}
        >
        <div className="flex items-center space-x-2">
          <span>{format(new Date(message.createdAt), 'HH:mm')}</span>
          {message.sentiment && <SentimentIcon sentiment={message.sentiment} />}
        </div>

        {!isInbound && message.deliveryStatus && (
          <span className="capitalize">{message.deliveryStatus}</span>
        )}
      </div>

      {/* Intent Badge */}
      {message.intent && isInbound && (
        <div className="mt-2">
          <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
            Intent: {message.intent}
          </span>
        </div>
      )}
    </div>
    </div >
  );
};

// ==================== Main Component ====================

export default function ConversationThread({
  conversation,
  onSendMessage,
  onClose,
}: ConversationThreadProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load messages
  useEffect(() => {
    loadMessages();
  }, [conversation.id]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call
      const response = await fetch(
        `/api/v1/conversations/${conversation.id}/messages`
      );
      const data = await response.json();
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    try {
      // TODO: Replace with actual API call
      await fetch(`/api/v1/conversations/${conversation.id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          textBody: newMessage,
          direction: 'outbound',
          contentType: 'text',
        }),
      });

      // Add optimistic message
      const optimisticMessage: Message = {
        id: `temp-${Date.now()}`,
        conversationId: conversation.id,
        direction: 'outbound',
        actorType: 'agent',
        contentType: 'text',
        textBody: newMessage,
        createdAt: new Date().toISOString(),
        deliveryStatus: 'sending',
      };

      setMessages([...messages, optimisticMessage]);
      setNewMessage('');

      if (onSendMessage) {
        onSendMessage(newMessage);
      }

      // Reload messages to get server confirmation
      setTimeout(loadMessages, 1000);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const filteredMessages = searchQuery
    ? messages.filter((msg) =>
      msg.textBody?.toLowerCase().includes(searchQuery.toLowerCase())
    )
    : messages;

  return (
    <div className="flex flex-col h-full bg-muted/30">
      {/* Header */}
      <div className="bg-card border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <ChannelIcon channel={conversation.channelType} />
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                {conversation.patientName || 'Unknown Patient'}
              </h2>
              <div className="flex items-center space-x-3 text-sm text-muted-foreground">
                <span className="capitalize">{conversation.status}</span>
                <span>•</span>
                <span className="capitalize">{conversation.channelType}</span>
                {conversation.lastMessageAt && (
                  <>
                    <span>•</span>
                    <span>
                      {formatDistanceToNow(new Date(conversation.lastMessageAt), {
                        addSuffix: true,
                      })}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search messages..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-input rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Close Button */}
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              >
                ×
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loading ? (
          <div className="flex justify-center items-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredMessages.length === 0 ? (
          <div className="flex flex-col justify-center items-center h-full text-gray-500">
            <MessageCircle className="w-12 h-12 mb-2" />
            <p>No messages yet</p>
          </div>
        ) : (
          <>
            {filteredMessages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Message Input */}
      {conversation.status !== 'closed' && (
        <div className="bg-card border-t border-border px-6 py-4">
          <div className="flex items-center space-x-3">
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <Paperclip className="w-5 h-5" />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <ImageIcon className="w-5 h-5" />
            </button>

            <input
              type="text"
              placeholder="Type a message..."
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              className="flex-1 px-4 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />

            <button
              onClick={handleSendMessage}
              disabled={!newMessage.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
