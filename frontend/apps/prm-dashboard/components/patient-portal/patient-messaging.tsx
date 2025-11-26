"use client";

// Patient Secure Messaging
// EPIC-UX-011: Patient Self-Service Portal - Journey 11.3

import React, { useEffect, useState, useRef } from "react";
import { format } from "date-fns";
import {
  MessageSquare, Send, Paperclip, Plus, AlertTriangle, User, FileText,
  ChevronLeft, Loader2, Download, X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  usePatientPortalStore,
  type MessageThread,
  type PortalMessage,
} from "@/lib/store/patient-portal-store";

// Emergency warning banner
function EmergencyWarning() {
  return (
    <Alert variant="destructive" className="rounded-none border-x-0">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription>
        For medical emergencies, call <strong>108</strong> or go to nearest emergency room.
        Messages are typically answered within 1-2 business days.
      </AlertDescription>
    </Alert>
  );
}

// Thread list item
interface ThreadItemProps {
  thread: MessageThread;
  isActive: boolean;
  onClick: () => void;
}

function ThreadItem({ thread, isActive, onClick }: ThreadItemProps) {
  return (
    <button
      className={cn(
        "w-full p-4 text-left border-b hover:bg-muted/50 transition-colors",
        isActive && "bg-primary/5 border-l-2 border-l-primary"
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-medium text-sm truncate">{thread.recipientName}</p>
            {thread.unreadCount > 0 && (
              <Badge className="h-5 px-1.5 text-xs">{thread.unreadCount}</Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground">{thread.recipientRole}</p>
          <p className="text-sm truncate mt-1">{thread.subject}</p>
        </div>
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {format(new Date(thread.lastMessageTime), "MMM d")}
        </span>
      </div>
    </button>
  );
}

// Message bubble
interface MessageBubbleProps {
  message: PortalMessage;
  isOwn: boolean;
}

function MessageBubble({ message, isOwn }: MessageBubbleProps) {
  return (
    <div className={cn("flex flex-col", isOwn ? "items-end" : "items-start")}>
      <div className="flex items-center gap-2 mb-1">
        {!isOwn && (
          <>
            <Avatar className="h-6 w-6">
              <AvatarFallback className="text-xs">
                {message.senderName.split(" ").map((n) => n[0]).join("").slice(0, 2)}
              </AvatarFallback>
            </Avatar>
            <span className="text-xs text-muted-foreground">{message.senderName}</span>
          </>
        )}
        {isOwn && <span className="text-xs text-muted-foreground">You</span>}
      </div>
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3",
          isOwn ? "bg-primary text-primary-foreground rounded-br-sm" : "bg-muted rounded-bl-sm"
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.attachments.map((att, i) => (
              <a
                key={i}
                href={att.url}
                className={cn(
                  "flex items-center gap-2 text-xs p-2 rounded",
                  isOwn ? "bg-primary-foreground/10 text-primary-foreground" : "bg-background"
                )}
              >
                <FileText className="h-4 w-4" />
                {att.name}
                <Download className="h-3 w-3 ml-auto" />
              </a>
            ))}
          </div>
        )}
      </div>
      <span className="text-[10px] text-muted-foreground mt-1 px-2">
        {format(new Date(message.timestamp), "h:mm a")}
      </span>
    </div>
  );
}

// New message dialog
interface NewMessageDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSend: (recipientId: string, subject: string, content: string) => void;
}

function NewMessageDialog({ open, onOpenChange, onSend }: NewMessageDialogProps) {
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [content, setContent] = useState("");

  const handleSend = () => {
    if (recipient && subject && content) {
      onSend(recipient, subject, content);
      setRecipient("");
      setSubject("");
      setContent("");
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>New Message</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <EmergencyWarning />
          <div className="space-y-2">
            <Label>To</Label>
            <Select value={recipient} onValueChange={setRecipient}>
              <SelectTrigger><SelectValue placeholder="Select recipient..." /></SelectTrigger>
              <SelectContent>
                <SelectItem value="dr-sharma">Dr. Sharma's Office (Cardiology)</SelectItem>
                <SelectItem value="dr-mehta">Dr. Mehta's Office (Endocrinology)</SelectItem>
                <SelectItem value="billing">Billing Department</SelectItem>
                <SelectItem value="appointments">Appointments</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Subject</Label>
            <Input
              placeholder="What is this about?"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Message</Label>
            <Textarea
              placeholder="Type your message..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={5}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSend} disabled={!recipient || !subject || !content}>
            <Send className="h-4 w-4 mr-2" />Send Message
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Message input
interface MessageInputProps {
  onSend: (content: string) => void;
  isSending: boolean;
}

function MessageInput({ onSend, isSending }: MessageInputProps) {
  const [message, setMessage] = useState("");

  const handleSend = () => {
    if (message.trim()) {
      onSend(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 border-t bg-background">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon">
          <Paperclip className="h-4 w-4" />
        </Button>
        <Input
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1"
          disabled={isSending}
        />
        <Button onClick={handleSend} disabled={!message.trim() || isSending}>
          {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}

// Main Patient Messaging Component
export function PatientMessaging() {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showNewMessage, setShowNewMessage] = useState(false);
  const [isMobileThreadView, setIsMobileThreadView] = useState(false);

  const {
    patient,
    messageThreads,
    activeThread,
    isLoadingMessages,
    isSendingMessage,
    fetchMessageThreads,
    selectThread,
    sendMessage,
    createNewThread,
  } = usePatientPortalStore();

  useEffect(() => { fetchMessageThreads(); }, [fetchMessageThreads]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeThread?.messages]);

  const handleSendMessage = async (content: string) => {
    if (activeThread) {
      await sendMessage(activeThread.id, content);
    }
  };

  const handleNewMessage = async (recipientId: string, subject: string, content: string) => {
    await createNewThread(recipientId, subject, content);
  };

  const totalUnread = messageThreads.reduce((sum, t) => sum + t.unreadCount, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <MessageSquare className="h-6 w-6" />Messages
          {totalUnread > 0 && <Badge>{totalUnread} unread</Badge>}
        </h1>
        <Button onClick={() => setShowNewMessage(true)}>
          <Plus className="h-4 w-4 mr-2" />New Message
        </Button>
      </div>

      <div className="border rounded-lg overflow-hidden h-[calc(100vh-16rem)]">
        <div className="flex h-full">
          {/* Thread list */}
          <div className={cn(
            "w-80 border-r flex flex-col",
            isMobileThreadView && activeThread && "hidden md:flex"
          )}>
            <div className="p-4 border-b">
              <Input placeholder="Search messages..." className="text-sm" />
            </div>
            <ScrollArea className="flex-1">
              {isLoadingMessages ? (
                <div className="p-4 text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                </div>
              ) : messageThreads.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  <p>No messages yet</p>
                </div>
              ) : (
                messageThreads.map((thread) => (
                  <ThreadItem
                    key={thread.id}
                    thread={thread}
                    isActive={activeThread?.id === thread.id}
                    onClick={() => {
                      selectThread(thread.id);
                      setIsMobileThreadView(true);
                    }}
                  />
                ))
              )}
            </ScrollArea>
          </div>

          {/* Message view */}
          <div className={cn(
            "flex-1 flex flex-col",
            !activeThread && "hidden md:flex"
          )}>
            {activeThread ? (
              <>
                {/* Header */}
                <div className="p-4 border-b flex items-center gap-3">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="md:hidden"
                    onClick={() => setIsMobileThreadView(false)}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Avatar>
                    <AvatarFallback>
                      {activeThread.recipientName.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-semibold">{activeThread.recipientName}</p>
                    <p className="text-xs text-muted-foreground">{activeThread.subject}</p>
                  </div>
                </div>

                {/* Emergency warning */}
                <EmergencyWarning />

                {/* Messages */}
                <ScrollArea className="flex-1 p-4">
                  <div className="space-y-4">
                    {activeThread.messages.map((msg) => (
                      <MessageBubble
                        key={msg.id}
                        message={msg}
                        isOwn={msg.senderRole === "patient"}
                      />
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                </ScrollArea>

                {/* Input */}
                <MessageInput onSend={handleSendMessage} isSending={isSendingMessage} />
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-30" />
                  <p>Select a conversation to view messages</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <NewMessageDialog
        open={showNewMessage}
        onOpenChange={setShowNewMessage}
        onSend={handleNewMessage}
      />
    </div>
  );
}

export default PatientMessaging;
