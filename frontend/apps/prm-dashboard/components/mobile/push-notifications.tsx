"use client";

// Push Notifications - Notification Management
// EPIC-UX-012: Mobile Applications - Journey 12.7

import React, { useState, useEffect } from "react";
import { format, formatDistanceToNow, isToday, isYesterday } from "date-fns";
import {
  Bell, BellOff, Calendar, MessageSquare, Pill, FileText, CreditCard,
  AlertCircle, Check, Trash2, Settings, ChevronRight, Clock,
  Video, Stethoscope, RefreshCw, X, Filter, CheckCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { useMobileStore, type PushNotification } from "@/lib/store/mobile-store";

// Notification type configuration
const notificationConfig: Record<PushNotification["type"], { icon: typeof Bell; color: string; bgColor: string; label: string }> = {
  appointment: { icon: Calendar, color: "text-blue-600", bgColor: "bg-blue-50", label: "Appointment" },
  telehealth: { icon: Video, color: "text-green-600", bgColor: "bg-green-50", label: "Telehealth" },
  message: { icon: MessageSquare, color: "text-purple-600", bgColor: "bg-purple-50", label: "Message" },
  lab_result: { icon: FileText, color: "text-orange-600", bgColor: "bg-orange-50", label: "Lab Result" },
  medication: { icon: Pill, color: "text-amber-600", bgColor: "bg-amber-50", label: "Medication" },
  bill: { icon: CreditCard, color: "text-slate-600", bgColor: "bg-slate-50", label: "Billing" },
  alert: { icon: AlertCircle, color: "text-red-600", bgColor: "bg-red-50", label: "Alert" },
  consult: { icon: Stethoscope, color: "text-teal-600", bgColor: "bg-teal-50", label: "Consult" },
};

// Notification item
interface NotificationItemProps {
  notification: PushNotification;
  onRead: () => void;
  onDelete: () => void;
  onAction: () => void;
}

function NotificationItem({ notification, onRead, onDelete, onAction }: NotificationItemProps) {
  const config = notificationConfig[notification.type];
  const Icon = config.icon;

  const getTimeLabel = (timestamp: string) => {
    const date = new Date(timestamp);
    if (isToday(date)) {
      return formatDistanceToNow(date, { addSuffix: true });
    } else if (isYesterday(date)) {
      return `Yesterday at ${format(date, "h:mm a")}`;
    }
    return format(date, "MMM d 'at' h:mm a");
  };

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-4 border-b last:border-b-0 transition-colors",
        !notification.read && "bg-primary/5"
      )}
    >
      <div className={cn("h-10 w-10 rounded-full flex items-center justify-center shrink-0", config.bgColor)}>
        <Icon className={cn("h-5 w-5", config.color)} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className={cn("font-medium text-sm truncate", !notification.read && "font-semibold")}>
                {notification.title}
              </p>
              {!notification.read && <div className="h-2 w-2 rounded-full bg-primary shrink-0" />}
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2 mt-0.5">{notification.body}</p>
            <p className="text-xs text-muted-foreground mt-1">
              <Clock className="h-3 w-3 inline mr-1" />
              {getTimeLabel(notification.timestamp)}
            </p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
                <Settings className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {!notification.read && (
                <DropdownMenuItem onClick={onRead}>
                  <Check className="h-4 w-4 mr-2" /> Mark as read
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={onDelete} className="text-red-600">
                <Trash2 className="h-4 w-4 mr-2" /> Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        {notification.actionUrl && (
          <Button variant="link" size="sm" className="h-auto p-0 mt-2" onClick={onAction}>
            View Details <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        )}
      </div>
    </div>
  );
}

// Notification group by date
interface NotificationGroupProps {
  label: string;
  notifications: PushNotification[];
  onRead: (id: string) => void;
  onDelete: (id: string) => void;
}

function NotificationGroup({ label, notifications, onRead, onDelete }: NotificationGroupProps) {
  return (
    <div>
      <div className="sticky top-0 bg-background/95 backdrop-blur px-4 py-2 border-b">
        <p className="text-xs font-medium text-muted-foreground uppercase">{label}</p>
      </div>
      {notifications.map((notif) => (
        <NotificationItem
          key={notif.id}
          notification={notif}
          onRead={() => onRead(notif.id)}
          onDelete={() => onDelete(notif.id)}
          onAction={() => {}}
        />
      ))}
    </div>
  );
}

// Notification preferences
interface NotificationPreference {
  type: PushNotification["type"];
  enabled: boolean;
  sound: boolean;
  badge: boolean;
}

function NotificationPreferences({
  preferences,
  onUpdate,
}: {
  preferences: NotificationPreference[];
  onUpdate: (type: PushNotification["type"], updates: Partial<NotificationPreference>) => void;
}) {
  return (
    <div className="space-y-4">
      {preferences.map((pref) => {
        const config = notificationConfig[pref.type];
        const Icon = config.icon;
        return (
          <div key={pref.type} className="p-4 rounded-lg border">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={cn("h-8 w-8 rounded-full flex items-center justify-center", config.bgColor)}>
                  <Icon className={cn("h-4 w-4", config.color)} />
                </div>
                <div>
                  <p className="font-medium text-sm">{config.label}</p>
                </div>
              </div>
              <Switch
                checked={pref.enabled}
                onCheckedChange={(enabled) => onUpdate(pref.type, { enabled })}
              />
            </div>
            {pref.enabled && (
              <div className="flex gap-4 ml-11">
                <label className="flex items-center gap-2 text-sm">
                  <Switch
                    checked={pref.sound}
                    onCheckedChange={(sound) => onUpdate(pref.type, { sound })}
                    className="scale-75"
                  />
                  <span className="text-muted-foreground">Sound</span>
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <Switch
                    checked={pref.badge}
                    onCheckedChange={(badge) => onUpdate(pref.type, { badge })}
                    className="scale-75"
                  />
                  <span className="text-muted-foreground">Badge</span>
                </label>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// Main Push Notifications Component
export function PushNotificationsView() {
  const [activeTab, setActiveTab] = useState("all");
  const [showSettings, setShowSettings] = useState(false);
  const [filterType, setFilterType] = useState<PushNotification["type"] | "all">("all");

  const {
    notifications,
    unreadCount,
    pushEnabled,
    fetchNotifications,
    markNotificationRead,
    clearAllNotifications,
    enablePushNotifications,
  } = useMobileStore();

  const [preferences, setPreferences] = useState<NotificationPreference[]>([
    { type: "appointment", enabled: true, sound: true, badge: true },
    { type: "telehealth", enabled: true, sound: true, badge: true },
    { type: "message", enabled: true, sound: true, badge: true },
    { type: "lab_result", enabled: true, sound: true, badge: true },
    { type: "medication", enabled: true, sound: true, badge: true },
    { type: "bill", enabled: true, sound: false, badge: true },
    { type: "alert", enabled: true, sound: true, badge: true },
    { type: "consult", enabled: true, sound: true, badge: true },
  ]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleUpdatePreference = (
    type: PushNotification["type"],
    updates: Partial<NotificationPreference>
  ) => {
    setPreferences((prev) =>
      prev.map((p) => (p.type === type ? { ...p, ...updates } : p))
    );
  };

  const handleDeleteNotification = (id: string) => {
    // In real app, would call a delete action
    console.log("Delete notification:", id);
  };

  const handleMarkAllRead = () => {
    notifications.forEach((n) => {
      if (!n.read) markNotificationRead(n.id);
    });
  };

  // Filter and group notifications
  const filteredNotifications = notifications.filter(
    (n) => filterType === "all" || n.type === filterType
  );

  const unreadNotifications = filteredNotifications.filter((n) => !n.read);
  const readNotifications = filteredNotifications.filter((n) => n.read);

  const groupByDate = (notifs: PushNotification[]) => {
    const today: PushNotification[] = [];
    const yesterday: PushNotification[] = [];
    const older: PushNotification[] = [];

    notifs.forEach((n) => {
      const date = new Date(n.timestamp);
      if (isToday(date)) today.push(n);
      else if (isYesterday(date)) yesterday.push(n);
      else older.push(n);
    });

    return { today, yesterday, older };
  };

  const grouped = groupByDate(filteredNotifications);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background border-b">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Bell className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Notifications</h1>
              {unreadCount > 0 && (
                <p className="text-sm text-muted-foreground">{unreadCount} unread</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Filter className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setFilterType("all")}>
                  All Notifications
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {Object.entries(notificationConfig).map(([type, config]) => (
                  <DropdownMenuItem
                    key={type}
                    onClick={() => setFilterType(type as PushNotification["type"])}
                  >
                    <config.icon className={cn("h-4 w-4 mr-2", config.color)} />
                    {config.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            <Button variant="ghost" size="icon" onClick={() => setShowSettings(true)}>
              <Settings className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Filter badge */}
        {filterType !== "all" && (
          <div className="px-4 pb-3">
            <Badge variant="secondary" className="gap-1">
              {notificationConfig[filterType].label}
              <button onClick={() => setFilterType("all")}>
                <X className="h-3 w-3" />
              </button>
            </Badge>
          </div>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="px-4 pt-2">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="unread">
              Unread
              {unreadCount > 0 && (
                <Badge variant="secondary" className="ml-2 h-5 w-5 p-0 justify-center">
                  {unreadCount}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="all" className="mt-0">
          {/* Quick Actions */}
          {unreadCount > 0 && (
            <div className="p-4 border-b">
              <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
                <CheckCircle className="h-4 w-4 mr-2" /> Mark all as read
              </Button>
            </div>
          )}

          <ScrollArea className="h-[calc(100vh-200px)]">
            {filteredNotifications.length === 0 ? (
              <div className="py-12 text-center">
                <Bell className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="font-medium">No notifications</p>
                <p className="text-sm text-muted-foreground">You're all caught up!</p>
              </div>
            ) : (
              <>
                {grouped.today.length > 0 && (
                  <NotificationGroup
                    label="Today"
                    notifications={grouped.today}
                    onRead={markNotificationRead}
                    onDelete={handleDeleteNotification}
                  />
                )}
                {grouped.yesterday.length > 0 && (
                  <NotificationGroup
                    label="Yesterday"
                    notifications={grouped.yesterday}
                    onRead={markNotificationRead}
                    onDelete={handleDeleteNotification}
                  />
                )}
                {grouped.older.length > 0 && (
                  <NotificationGroup
                    label="Earlier"
                    notifications={grouped.older}
                    onRead={markNotificationRead}
                    onDelete={handleDeleteNotification}
                  />
                )}
              </>
            )}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="unread" className="mt-0">
          <ScrollArea className="h-[calc(100vh-200px)]">
            {unreadNotifications.length === 0 ? (
              <div className="py-12 text-center">
                <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
                <p className="font-medium">All caught up!</p>
                <p className="text-sm text-muted-foreground">No unread notifications</p>
              </div>
            ) : (
              unreadNotifications.map((notif) => (
                <NotificationItem
                  key={notif.id}
                  notification={notif}
                  onRead={() => markNotificationRead(notif.id)}
                  onDelete={() => handleDeleteNotification(notif.id)}
                  onAction={() => {}}
                />
              ))
            )}
          </ScrollArea>
        </TabsContent>
      </Tabs>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent className="max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Notification Settings</DialogTitle>
            <DialogDescription>Customize your notification preferences</DialogDescription>
          </DialogHeader>

          {/* Master toggle */}
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-3">
              {pushEnabled ? (
                <Bell className="h-5 w-5 text-primary" />
              ) : (
                <BellOff className="h-5 w-5 text-muted-foreground" />
              )}
              <div>
                <p className="font-medium">Push Notifications</p>
                <p className="text-sm text-muted-foreground">
                  {pushEnabled ? "Enabled" : "Disabled"}
                </p>
              </div>
            </div>
            <Switch
              checked={pushEnabled}
              onCheckedChange={(enabled) => enablePushNotifications(enabled)}
            />
          </div>

          {pushEnabled && (
            <NotificationPreferences
              preferences={preferences}
              onUpdate={handleUpdatePreference}
            />
          )}

          {/* Danger Zone */}
          <div className="pt-4 border-t">
            <Button
              variant="outline"
              className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
              onClick={() => {
                clearAllNotifications();
                setShowSettings(false);
              }}
            >
              <Trash2 className="h-4 w-4 mr-2" /> Clear All Notifications
            </Button>
          </div>

          <DialogFooter>
            <Button onClick={() => setShowSettings(false)}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Notification bell widget with badge
export function NotificationBellWidget({ onClick }: { onClick: () => void }) {
  const { unreadCount } = useMobileStore();

  return (
    <Button variant="ghost" size="icon" className="relative" onClick={onClick}>
      <Bell className="h-5 w-5" />
      {unreadCount > 0 && (
        <span className="absolute top-1 right-1 h-4 w-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center">
          {unreadCount > 9 ? "9+" : unreadCount}
        </span>
      )}
    </Button>
  );
}

// Compact notification preview
export function NotificationPreview() {
  const { notifications, unreadCount } = useMobileStore();
  const latestUnread = notifications.filter((n) => !n.read).slice(0, 3);

  if (latestUnread.length === 0) {
    return (
      <div className="p-3 text-center text-sm text-muted-foreground">
        No new notifications
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {latestUnread.map((notif) => {
        const config = notificationConfig[notif.type];
        const Icon = config.icon;
        return (
          <div key={notif.id} className="flex items-center gap-2 p-2 rounded-lg bg-muted/50">
            <Icon className={cn("h-4 w-4 shrink-0", config.color)} />
            <p className="text-sm truncate flex-1">{notif.title}</p>
          </div>
        );
      })}
      {unreadCount > 3 && (
        <p className="text-xs text-muted-foreground text-center">
          +{unreadCount - 3} more
        </p>
      )}
    </div>
  );
}

export default PushNotificationsView;
