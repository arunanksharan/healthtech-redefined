"use client";

// Provider Messaging Interface
// EPIC-UX-010: Provider Collaboration Hub - Journey 10.1

import React, { useEffect, useState, useRef } from "react";
import { format } from "date-fns";
import {
  MessageSquare, Search, Plus, Send, Paperclip, User, Users, Building2,
  Check, CheckCheck, Circle, MoreVertical, Pin, BellOff, X, Phone, Video,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandInput, CommandList, CommandItem, CommandEmpty, CommandGroup } from "@/components/ui/command";
import {
  useCollaborationStore,
  type Conversation,
  type Message,
  type User as UserType,
  type PresenceStatus,
  type PatientContext,
} from "@/lib/store/collaboration-store";

// Presence indicator
function PresenceIndicator({ status, size = "sm" }: { status: PresenceStatus; size?: "sm" | "lg" }) {
  const colors = {
    online: "bg-green-500",
    busy: "bg-amber-500",
    away: "bg-gray-400",
    offline: "bg-gray-300",
  };
  const sizeClass = size === "lg" ? "h-3 w-3" : "h-2 w-2";
  return <div className={cn("rounded-full", sizeClass, colors[status])} />;
}

// Conversation list item
interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  currentUserId: string;
  onClick: () => void;
}

function ConversationItem({ conversation, isActive, currentUserId, onClick }: ConversationItemProps) {
  const otherParticipant = conversation.participants.find((p) => p.id !== currentUserId);
  const displayName = conversation.name || otherParticipant?.name || "Unknown";
  const presence = otherParticipant?.presence || "offline";

  return (
    <div
      className={cn(
        "p-3 cursor-pointer hover:bg-muted/50 border-b transition-colors",
        isActive && "bg-primary/5 border-l-2 border-l-primary"
      )}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div className="relative">
          <Avatar className="h-10 w-10">
            <AvatarFallback className={cn(conversation.type === "department" ? "bg-blue-100 text-blue-700" : "bg-primary/10")}>
              {conversation.type === "department" ? <Building2 className="h-5 w-5" /> : conversation.type === "group" ? <Users className="h-5 w-5" /> : displayName.split(" ").map((n) => n[0]).join("").slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          {conversation.type === "direct" && (
            <div className="absolute -bottom-0.5 -right-0.5">
              <PresenceIndicator status={presence} />
            </div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="font-medium text-sm truncate">{displayName}</span>
            {conversation.lastMessage && (
              <span className="text-xs text-muted-foreground">
                {format(new Date(conversation.lastMessage.timestamp), "h:mm a")}
              </span>
            )}
          </div>
          {conversation.lastMessage && (
            <p className="text-xs text-muted-foreground truncate mt-0.5">
              {conversation.lastMessage.senderId === currentUserId ? "You: " : ""}
              {conversation.lastMessage.content}
            </p>
          )}
          {conversation.patientContext && (
            <Badge variant="outline" className="mt-1 text-xs">
              <User className="h-3 w-3 mr-1" />
              {conversation.patientContext.name}
            </Badge>
          )}
        </div>
        {conversation.unreadCount > 0 && (
          <Badge className="h-5 w-5 p-0 flex items-center justify-center text-xs">
            {conversation.unreadCount}
          </Badge>
        )}
      </div>
    </div>
  );
}

// Message bubble
interface MessageBubbleProps {
  message: Message;
  isOwn: boolean;
  showSender: boolean;
}

function MessageBubble({ message, isOwn, showSender }: MessageBubbleProps) {
  return (
    <div className={cn("flex flex-col", isOwn ? "items-end" : "items-start")}>
      {showSender && !isOwn && (
        <span className="text-xs text-muted-foreground mb-1 ml-2">{message.senderName}</span>
      )}
      {message.type === "patient_link" && message.patientContext && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 mb-1 max-w-xs">
          <p className="text-xs text-blue-700 flex items-center gap-1">
            <User className="h-3 w-3" />
            Re: {message.patientContext.name} (MRN: {message.patientContext.mrn})
          </p>
        </div>
      )}
      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-4 py-2",
          isOwn ? "bg-primary text-primary-foreground rounded-br-sm" : "bg-muted rounded-bl-sm"
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
      </div>
      <div className="flex items-center gap-1 mt-0.5 px-2">
        <span className="text-[10px] text-muted-foreground">
          {format(new Date(message.timestamp), "h:mm a")}
        </span>
        {isOwn && (
          message.readBy.length > 1 ? (
            <CheckCheck className="h-3 w-3 text-blue-500" />
          ) : (
            <Check className="h-3 w-3 text-muted-foreground" />
          )
        )}
      </div>
    </div>
  );
}

// Chat header
interface ChatHeaderProps {
  conversation: Conversation;
  currentUserId: string;
  onClose?: () => void;
}

function ChatHeader({ conversation, currentUserId, onClose }: ChatHeaderProps) {
  const otherParticipant = conversation.participants.find((p) => p.id !== currentUserId);
  const displayName = conversation.name || otherParticipant?.name || "Unknown";
  const presence = otherParticipant?.presence;

  return (
    <div className="flex items-center justify-between p-4 border-b">
      <div className="flex items-center gap-3">
        <Avatar className="h-10 w-10">
          <AvatarFallback>
            {conversation.type === "department" ? <Building2 className="h-5 w-5" /> : displayName.split(" ").map((n) => n[0]).join("").slice(0, 2)}
          </AvatarFallback>
        </Avatar>
        <div>
          <h3 className="font-semibold">{displayName}</h3>
          {conversation.type === "direct" && presence && (
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <PresenceIndicator status={presence} />
              {presence.charAt(0).toUpperCase() + presence.slice(1)}
            </p>
          )}
          {conversation.type !== "direct" && (
            <p className="text-xs text-muted-foreground">
              {conversation.participants.length} members
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon"><Phone className="h-4 w-4" /></Button>
        <Button variant="ghost" size="icon"><Video className="h-4 w-4" /></Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon"><MoreVertical className="h-4 w-4" /></Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem><Pin className="h-4 w-4 mr-2" />Pin conversation</DropdownMenuItem>
            <DropdownMenuItem><BellOff className="h-4 w-4 mr-2" />Mute notifications</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

// Message input
interface MessageInputProps {
  onSend: (content: string) => void;
  onAttach: () => void;
  onLinkPatient: () => void;
}

function MessageInput({ onSend, onAttach, onLinkPatient }: MessageInputProps) {
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
    <div className="p-4 border-t">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={onAttach}>
          <Paperclip className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={onLinkPatient}>
          <User className="h-4 w-4" />
        </Button>
        <Input
          placeholder="Type a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1"
        />
        <Button onClick={handleSend} disabled={!message.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// New conversation dialog
interface NewConversationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onlineUsers: UserType[];
  currentUserId: string;
  onCreateConversation: (participantIds: string[]) => void;
}

function NewConversationDialog({ open, onOpenChange, onlineUsers, currentUserId, onCreateConversation }: NewConversationDialogProps) {
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const availableUsers = onlineUsers.filter((u) => u.id !== currentUserId);

  const handleCreate = () => {
    if (selectedUsers.length > 0) {
      onCreateConversation(selectedUsers);
      setSelectedUsers([]);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>New Conversation</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Select colleagues to message:</p>
          <div className="space-y-2">
            {availableUsers.map((user) => (
              <div
                key={user.id}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-muted/50",
                  selectedUsers.includes(user.id) && "border-primary bg-primary/5"
                )}
                onClick={() => setSelectedUsers((prev) =>
                  prev.includes(user.id) ? prev.filter((id) => id !== user.id) : [...prev, user.id]
                )}
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback>{user.name.split(" ").map((n) => n[0]).join("")}</AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <p className="text-sm font-medium">{user.name}</p>
                  <p className="text-xs text-muted-foreground">{user.role} - {user.department}</p>
                </div>
                <PresenceIndicator status={user.presence} size="lg" />
              </div>
            ))}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleCreate} disabled={selectedUsers.length === 0}>Start Conversation</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Patient link popover
interface PatientLinkPopoverProps {
  onSelect: (patient: PatientContext) => void;
}

function PatientLinkPopover({ onSelect }: PatientLinkPopoverProps) {
  const [open, setOpen] = useState(false);
  const mockPatients: PatientContext[] = [
    { id: "p1", mrn: "MRN-12345", name: "John Doe", age: 59, gender: "Male", room: "301", primaryDiagnosis: "CHF" },
    { id: "p2", mrn: "MRN-67890", name: "Mary Johnson", age: 45, gender: "Female", room: "205", primaryDiagnosis: "T2DM" },
    { id: "p3", mrn: "MRN-11111", name: "Robert Smith", age: 72, gender: "Male", room: "102", primaryDiagnosis: "COPD" },
  ];

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon"><User className="h-4 w-4" /></Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" align="start">
        <Command>
          <CommandInput placeholder="Search patients..." />
          <CommandList>
            <CommandEmpty>No patients found.</CommandEmpty>
            <CommandGroup heading="Recent Patients">
              {mockPatients.map((patient) => (
                <CommandItem
                  key={patient.id}
                  onSelect={() => {
                    onSelect(patient);
                    setOpen(false);
                  }}
                >
                  <div className="flex-1">
                    <p className="font-medium">{patient.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {patient.mrn} | Room {patient.room} | {patient.primaryDiagnosis}
                    </p>
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

// Main Messaging Interface
export function MessagingInterface() {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showNewConversation, setShowNewConversation] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const {
    currentUser,
    conversations,
    activeConversationId,
    messages,
    onlineUsers,
    isLoadingConversations,
    isLoadingMessages,
    fetchConversations,
    selectConversation,
    sendMessage,
    createConversation,
    fetchOnlineUsers,
  } = useCollaborationStore();

  useEffect(() => {
    fetchConversations();
    fetchOnlineUsers();
  }, [fetchConversations, fetchOnlineUsers]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeConversationId]);

  const activeConversation = conversations.find((c) => c.id === activeConversationId);
  const activeMessages = activeConversationId ? messages[activeConversationId] || [] : [];

  const filteredConversations = conversations.filter((c) => {
    if (!searchQuery) return true;
    const searchLower = searchQuery.toLowerCase();
    return (
      c.name?.toLowerCase().includes(searchLower) ||
      c.participants.some((p) => p.name.toLowerCase().includes(searchLower))
    );
  });

  const handleSendMessage = (content: string) => {
    if (activeConversationId) {
      sendMessage(activeConversationId, { content, type: "text" });
    }
  };

  const handleLinkPatient = (patient: PatientContext) => {
    if (activeConversationId) {
      sendMessage(activeConversationId, {
        content: `Re: ${patient.name} (MRN: ${patient.mrn})`,
        type: "patient_link",
        patientContext: patient,
      });
    }
  };

  const handleCreateConversation = async (participantIds: string[]) => {
    const convId = await createConversation(participantIds);
    if (convId) selectConversation(convId);
  };

  return (
    <div className="flex h-[calc(100vh-12rem)] border rounded-lg overflow-hidden">
      {/* Conversations sidebar */}
      <div className="w-80 border-r flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />Messages
            </h2>
            <Button size="sm" onClick={() => setShowNewConversation(true)}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        <ScrollArea className="flex-1">
          {isLoadingConversations ? (
            <div className="p-4 text-center text-muted-foreground">Loading...</div>
          ) : filteredConversations.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">No conversations</div>
          ) : (
            filteredConversations.map((conv) => (
              <ConversationItem
                key={conv.id}
                conversation={conv}
                isActive={conv.id === activeConversationId}
                currentUserId={currentUser?.id || ""}
                onClick={() => selectConversation(conv.id)}
              />
            ))
          )}
        </ScrollArea>

        <div className="p-3 border-t bg-muted/30">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="flex items-center gap-1"><div className="h-2 w-2 rounded-full bg-green-500" /><span>Direct</span></div>
            <div className="flex items-center gap-1"><Users className="h-3 w-3" /><span>Group</span></div>
            <div className="flex items-center gap-1"><Building2 className="h-3 w-3" /><span>Department</span></div>
          </div>
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {activeConversation ? (
          <>
            <ChatHeader conversation={activeConversation} currentUserId={currentUser?.id || ""} />
            <ScrollArea className="flex-1 p-4">
              {isLoadingMessages ? (
                <div className="text-center text-muted-foreground">Loading messages...</div>
              ) : (
                <div className="space-y-4">
                  {activeMessages.map((msg, i) => {
                    const isOwn = msg.senderId === currentUser?.id;
                    const showSender = !isOwn && (i === 0 || activeMessages[i - 1].senderId !== msg.senderId);
                    return <MessageBubble key={msg.id} message={msg} isOwn={isOwn} showSender={showSender} />;
                  })}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </ScrollArea>
            <div className="p-4 border-t">
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="icon"><Paperclip className="h-4 w-4" /></Button>
                <PatientLinkPopover onSelect={handleLinkPatient} />
                <Input
                  placeholder="Type a message..."
                  className="flex-1"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      const input = e.currentTarget;
                      if (input.value.trim()) {
                        handleSendMessage(input.value.trim());
                        input.value = "";
                      }
                    }
                  }}
                />
                <Button><Send className="h-4 w-4" /></Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-30" />
              <p>Select a conversation to start messaging</p>
            </div>
          </div>
        )}
      </div>

      <NewConversationDialog
        open={showNewConversation}
        onOpenChange={setShowNewConversation}
        onlineUsers={onlineUsers}
        currentUserId={currentUser?.id || ""}
        onCreateConversation={handleCreateConversation}
      />
    </div>
  );
}

// Compact messages widget for dashboard
export function MessagesWidget() {
  const { conversations, fetchConversations, selectConversation } = useCollaborationStore();

  useEffect(() => { fetchConversations(); }, [fetchConversations]);

  const recentConversations = conversations.slice(0, 3);
  const unreadCount = conversations.reduce((sum, c) => sum + c.unreadCount, 0);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />Messages
          </CardTitle>
          {unreadCount > 0 && <Badge>{unreadCount} unread</Badge>}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {recentConversations.map((conv) => (
          <div
            key={conv.id}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 cursor-pointer"
            onClick={() => selectConversation(conv.id)}
          >
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs">
                {conv.name?.slice(0, 2) || conv.participants[0]?.name.split(" ").map((n) => n[0]).join("")}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{conv.name || conv.participants.map((p) => p.name).join(", ")}</p>
              {conv.lastMessage && <p className="text-xs text-muted-foreground truncate">{conv.lastMessage.content}</p>}
            </div>
            {conv.unreadCount > 0 && <Badge variant="secondary" className="h-5 w-5 p-0 flex items-center justify-center text-xs">{conv.unreadCount}</Badge>}
          </div>
        ))}
        <Button variant="ghost" className="w-full text-xs">View All Messages</Button>
      </CardContent>
    </Card>
  );
}

export default MessagingInterface;
