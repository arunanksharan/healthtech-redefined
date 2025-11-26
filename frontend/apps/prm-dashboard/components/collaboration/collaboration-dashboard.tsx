"use client";

// Provider Collaboration Hub Dashboard
// EPIC-UX-010: Unified collaboration interface

import React, { useEffect, useState } from "react";
import { format } from "date-fns";
import {
  MessageSquare, Stethoscope, FileText, Calendar, Users, Phone, Settings,
  Bell, Search, Plus, Circle, ChevronRight, Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useCollaborationStore, type PresenceStatus } from "@/lib/store/collaboration-store";
import { MessagingInterface, MessagesWidget } from "./messaging-interface";
import { ConsultationsDashboard, ConsultationsWidget } from "./consultation-request";
import { HandoffDashboard, HandoffsWidget } from "./sbar-handoff";
import { OnCallSchedule, OnCallWidget } from "./on-call-schedule";

// Presence status selector
function PresenceSelector() {
  const { currentUser, updatePresence } = useCollaborationStore();
  const [isOpen, setIsOpen] = useState(false);

  const statuses: { status: PresenceStatus; label: string; color: string }[] = [
    { status: "online", label: "Available", color: "bg-green-500" },
    { status: "busy", label: "Busy", color: "bg-amber-500" },
    { status: "away", label: "Away", color: "bg-gray-400" },
    { status: "offline", label: "Appear Offline", color: "bg-gray-300" },
  ];

  return (
    <div className="relative">
      <button
        className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Avatar className="h-8 w-8">
          <AvatarFallback>{currentUser?.name.split(" ").map((n) => n[0]).join("")}</AvatarFallback>
        </Avatar>
        <div className="text-left">
          <p className="text-sm font-medium">{currentUser?.name}</p>
          <div className="flex items-center gap-1">
            <div className={cn("h-2 w-2 rounded-full", statuses.find((s) => s.status === currentUser?.presence)?.color)} />
            <span className="text-xs text-muted-foreground capitalize">{currentUser?.presence}</span>
          </div>
        </div>
      </button>
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-48 bg-background border rounded-lg shadow-lg z-50">
          <div className="p-2">
            <p className="text-xs text-muted-foreground px-2 py-1">Set Status</p>
            {statuses.map(({ status, label, color }) => (
              <button
                key={status}
                className={cn(
                  "w-full flex items-center gap-2 px-2 py-2 rounded hover:bg-muted/50 text-sm",
                  currentUser?.presence === status && "bg-muted"
                )}
                onClick={() => {
                  updatePresence(status);
                  setIsOpen(false);
                }}
              >
                <div className={cn("h-2 w-2 rounded-full", color)} />
                {label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Online colleagues sidebar
function OnlineColleagues() {
  const { onlineUsers, fetchOnlineUsers } = useCollaborationStore();

  useEffect(() => { fetchOnlineUsers(); }, [fetchOnlineUsers]);

  const getPresenceColor = (presence: PresenceStatus) => {
    const colors = {
      online: "bg-green-500",
      busy: "bg-amber-500",
      away: "bg-gray-400",
      offline: "bg-gray-300",
    };
    return colors[presence];
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Online Now</CardTitle>
          <Badge variant="secondary">{onlineUsers.length}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-1">
        {onlineUsers.slice(0, 5).map((user) => (
          <div key={user.id} className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 cursor-pointer">
            <div className="relative">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs">{user.name.split(" ").map((n) => n[0]).join("")}</AvatarFallback>
              </Avatar>
              <div className={cn("absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-background", getPresenceColor(user.presence))} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user.name}</p>
              <p className="text-xs text-muted-foreground truncate">{user.role}</p>
            </div>
          </div>
        ))}
        {onlineUsers.length > 5 && (
          <Button variant="ghost" className="w-full text-xs">
            View All ({onlineUsers.length})
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

// Quick stats for dashboard
function QuickStats() {
  const { conversations, consultations, handoffs, currentUser } = useCollaborationStore();

  const unreadMessages = conversations.reduce((sum, c) => sum + c.unreadCount, 0);
  const pendingConsults = consultations.filter((c) => c.status === "pending").length;
  const pendingHandoffs = handoffs.filter((h) => h.toUserId === currentUser?.id && h.status === "pending_acknowledgment").length;

  const stats = [
    { label: "Unread Messages", value: unreadMessages, icon: MessageSquare, color: "text-blue-600" },
    { label: "Pending Consults", value: pendingConsults, icon: Stethoscope, color: "text-amber-600" },
    { label: "Pending Handoffs", value: pendingHandoffs, icon: FileText, color: "text-purple-600" },
  ];

  return (
    <div className="grid grid-cols-3 gap-4">
      {stats.map((stat) => (
        <Card key={stat.label}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className={cn("h-10 w-10 rounded-full bg-muted flex items-center justify-center", stat.color)}>
                <stat.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stat.value}</p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Activity feed
function ActivityFeed() {
  const { conversations, consultations, handoffs } = useCollaborationStore();

  // Combine and sort recent activity
  const activities: Array<{ type: string; title: string; time: Date; icon: typeof MessageSquare }> = [
    ...conversations.slice(0, 2).map((c) => ({
      type: "message",
      title: `New message in ${c.name || "conversation"}`,
      time: new Date(c.updatedAt),
      icon: MessageSquare,
    })),
    ...consultations.slice(0, 2).map((c) => ({
      type: "consultation",
      title: `${c.specialty} consult - ${c.status}`,
      time: new Date(c.createdAt),
      icon: Stethoscope,
    })),
    ...handoffs.slice(0, 2).map((h) => ({
      type: "handoff",
      title: `Handoff from ${h.fromUserName}`,
      time: new Date(h.createdAt),
      icon: FileText,
    })),
  ].sort((a, b) => b.time.getTime() - a.time.getTime()).slice(0, 5);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {activities.map((activity, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
              <activity.icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm">{activity.title}</p>
              <p className="text-xs text-muted-foreground">{format(activity.time, "h:mm a")}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// Main Collaboration Dashboard
export function CollaborationDashboard() {
  const [activeTab, setActiveTab] = useState("overview");

  const {
    fetchConversations,
    fetchConsultations,
    fetchHandoffs,
    fetchOnlineUsers,
    isLoadingConversations,
  } = useCollaborationStore();

  useEffect(() => {
    fetchConversations();
    fetchConsultations();
    fetchHandoffs();
    fetchOnlineUsers();
  }, [fetchConversations, fetchConsultations, fetchHandoffs, fetchOnlineUsers]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <Users className="h-6 w-6" />Provider Collaboration Hub
          </h1>
          <p className="text-sm text-muted-foreground">
            Real-time communication and care coordination
          </p>
        </div>
        <div className="flex items-center gap-4">
          <PresenceSelector />
          <Button variant="outline" size="icon">
            <Bell className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <Users className="h-4 w-4" />Overview
          </TabsTrigger>
          <TabsTrigger value="messages" className="gap-2">
            <MessageSquare className="h-4 w-4" />Messages
          </TabsTrigger>
          <TabsTrigger value="consultations" className="gap-2">
            <Stethoscope className="h-4 w-4" />Consultations
          </TabsTrigger>
          <TabsTrigger value="handoffs" className="gap-2">
            <FileText className="h-4 w-4" />Handoffs
          </TabsTrigger>
          <TabsTrigger value="oncall" className="gap-2">
            <Calendar className="h-4 w-4" />On-Call
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          {isLoadingConversations ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-12 gap-6">
              {/* Main content */}
              <div className="col-span-9 space-y-6">
                <QuickStats />
                <div className="grid grid-cols-2 gap-6">
                  <MessagesWidget />
                  <ConsultationsWidget />
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <HandoffsWidget />
                  <OnCallWidget />
                </div>
              </div>

              {/* Sidebar */}
              <div className="col-span-3 space-y-6">
                <OnlineColleagues />
                <ActivityFeed />
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="messages" className="mt-6">
          <MessagingInterface />
        </TabsContent>

        <TabsContent value="consultations" className="mt-6">
          <ConsultationsDashboard />
        </TabsContent>

        <TabsContent value="handoffs" className="mt-6">
          <HandoffDashboard />
        </TabsContent>

        <TabsContent value="oncall" className="mt-6">
          <OnCallSchedule />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Export compact dashboard widgets
export { MessagesWidget, ConsultationsWidget, HandoffsWidget, OnCallWidget };

export default CollaborationDashboard;
