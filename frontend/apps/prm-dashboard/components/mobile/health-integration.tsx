"use client";

// Health Integration - Apple Health / Google Fit Integration
// EPIC-UX-012: Mobile Applications - Journey 12.6

import React, { useState, useEffect } from "react";
import { format, subDays, startOfWeek, eachDayOfInterval } from "date-fns";
import {
  Heart, Activity, Moon, Scale, Droplet, Thermometer, ChevronRight,
  RefreshCw, Shield, AlertCircle, Check, Settings, Loader2,
  TrendingUp, TrendingDown, Minus, Calendar, Clock, Smartphone,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import {
  useMobileStore,
  type HealthIntegration as HealthIntegrationType,
  type HealthDataPoint,
} from "@/lib/store/mobile-store";

// Health metric card
interface HealthMetricCardProps {
  type: string;
  value: string | number;
  unit: string;
  trend?: "up" | "down" | "stable";
  trendValue?: string;
  lastUpdated: string;
  goal?: number;
  current?: number;
  onClick?: () => void;
}

function HealthMetricCard({
  type,
  value,
  unit,
  trend,
  trendValue,
  lastUpdated,
  goal,
  current,
  onClick,
}: HealthMetricCardProps) {
  const iconConfig: Record<string, { icon: typeof Heart; color: string; bgColor: string }> = {
    heart_rate: { icon: Heart, color: "text-red-500", bgColor: "bg-red-50" },
    blood_pressure: { icon: Activity, color: "text-purple-500", bgColor: "bg-purple-50" },
    steps: { icon: Activity, color: "text-green-500", bgColor: "bg-green-50" },
    weight: { icon: Scale, color: "text-blue-500", bgColor: "bg-blue-50" },
    sleep: { icon: Moon, color: "text-indigo-500", bgColor: "bg-indigo-50" },
    glucose: { icon: Droplet, color: "text-amber-500", bgColor: "bg-amber-50" },
  };

  const config = iconConfig[type] || { icon: Activity, color: "text-gray-500", bgColor: "bg-gray-50" };
  const Icon = config.icon;

  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const trendColor = type === "weight"
    ? (trend === "down" ? "text-green-500" : trend === "up" ? "text-red-500" : "text-muted-foreground")
    : (trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : "text-muted-foreground");

  return (
    <Card className="cursor-pointer hover:bg-muted/50 transition-colors" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={cn("h-10 w-10 rounded-full flex items-center justify-center", config.bgColor)}>
            <Icon className={cn("h-5 w-5", config.color)} />
          </div>
          <div className="flex-1">
            <p className="text-xs text-muted-foreground capitalize">{type.replace("_", " ")}</p>
            <div className="flex items-baseline gap-1">
              <p className="text-xl font-bold">{value}</p>
              <span className="text-sm text-muted-foreground">{unit}</span>
            </div>
            {trend && trendValue && (
              <div className={cn("flex items-center gap-1 text-xs", trendColor)}>
                <TrendIcon className="h-3 w-3" />
                <span>{trendValue}</span>
              </div>
            )}
            {goal && current !== undefined && (
              <div className="mt-2">
                <Progress value={(current / goal) * 100} className="h-1.5" />
                <p className="text-[10px] text-muted-foreground mt-1">{current.toLocaleString()} / {goal.toLocaleString()}</p>
              </div>
            )}
          </div>
        </div>
        <p className="text-[10px] text-muted-foreground mt-2">
          <Clock className="h-3 w-3 inline mr-1" />
          {lastUpdated}
        </p>
      </CardContent>
    </Card>
  );
}

// Weekly activity chart
interface WeeklyChartProps {
  data: Array<{ day: string; value: number }>;
  goal: number;
  unit: string;
}

function WeeklyChart({ data, goal, unit }: WeeklyChartProps) {
  const maxValue = Math.max(...data.map(d => d.value), goal);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">This Week</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between gap-2 h-24">
          {data.map((day, i) => {
            const height = (day.value / maxValue) * 100;
            const isGoalMet = day.value >= goal;
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div className="w-full h-20 bg-muted rounded-t relative">
                  <div
                    className={cn(
                      "absolute bottom-0 w-full rounded-t transition-all",
                      isGoalMet ? "bg-green-500" : "bg-primary"
                    )}
                    style={{ height: `${height}%` }}
                  />
                </div>
                <span className="text-[10px] text-muted-foreground">{day.day}</span>
              </div>
            );
          })}
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-muted-foreground">Goal: {goal.toLocaleString()} {unit}</span>
          <Badge variant="outline" className="text-xs">
            {data.filter(d => d.value >= goal).length}/7 days
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

// Permission toggle
interface PermissionToggleProps {
  label: string;
  description: string;
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  icon: typeof Heart;
}

function PermissionToggle({ label, description, enabled, onToggle, icon: Icon }: PermissionToggleProps) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg border">
      <div className="flex items-center gap-3">
        <Icon className="h-5 w-5 text-muted-foreground" />
        <div>
          <p className="text-sm font-medium">{label}</p>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
      <Switch checked={enabled} onCheckedChange={onToggle} />
    </div>
  );
}

// Connection status card
interface ConnectionCardProps {
  provider: "apple_health" | "google_fit";
  connected: boolean;
  lastSync?: string;
  onConnect: () => void;
  onDisconnect: () => void;
  onSync: () => void;
  isSyncing: boolean;
}

function ConnectionCard({
  provider,
  connected,
  lastSync,
  onConnect,
  onDisconnect,
  onSync,
  isSyncing,
}: ConnectionCardProps) {
  const providerConfig = {
    apple_health: { name: "Apple Health", icon: "🍎", color: "bg-black text-white" },
    google_fit: { name: "Google Fit", icon: "💚", color: "bg-green-500 text-white" },
  };

  const config = providerConfig[provider];

  return (
    <Card className={cn(connected && "border-green-200")}>
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          <div className={cn("h-12 w-12 rounded-xl flex items-center justify-center text-xl", config.color)}>
            {config.icon}
          </div>
          <div className="flex-1">
            <p className="font-semibold">{config.name}</p>
            {connected ? (
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">
                  <Check className="h-3 w-3 mr-1" /> Connected
                </Badge>
                {lastSync && (
                  <span className="text-xs text-muted-foreground">Synced {lastSync}</span>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Not connected</p>
            )}
          </div>
          {connected ? (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={onSync} disabled={isSyncing}>
                {isSyncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              </Button>
              <Button variant="ghost" size="sm" onClick={onDisconnect}>
                Disconnect
              </Button>
            </div>
          ) : (
            <Button onClick={onConnect}>Connect</Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Health detail modal
interface HealthDetailModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  type: string;
  data: HealthDataPoint[];
}

function HealthDetailModal({ open, onOpenChange, type, data }: HealthDetailModalProps) {
  const filteredData = data.filter(d => d.type === type);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="capitalize">{type.replace("_", " ")} History</DialogTitle>
          <DialogDescription>Your recent readings and trends</DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-[60vh]">
          <div className="space-y-2">
            {filteredData.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">No data available</p>
            ) : (
              filteredData.map((point, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div>
                    <p className="text-sm font-medium">{point.value} {point.unit}</p>
                    <p className="text-xs text-muted-foreground">
                      {format(new Date(point.timestamp), "MMM d, h:mm a")}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-xs capitalize">{point.source.replace("_", " ")}</Badge>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

// Main Health Integration Component
export function HealthIntegrationView() {
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  const [showPermissions, setShowPermissions] = useState(false);

  const {
    healthIntegration,
    recentHealthData,
    isHealthSyncing,
    setupHealthIntegration,
    updateHealthPermissions,
    syncHealthData,
  } = useMobileStore();

  // Generate weekly steps data
  const weekDays = eachDayOfInterval({
    start: startOfWeek(new Date()),
    end: new Date(),
  });
  const weeklySteps = weekDays.map((day, i) => ({
    day: format(day, "EEE"),
    value: Math.floor(Math.random() * 5000) + 5000 + (i * 500),
  }));

  // Get latest values for each metric
  const getLatestMetric = (type: string) => {
    const metric = recentHealthData.find(d => d.type === type);
    return metric || null;
  };

  const heartRate = getLatestMetric("heart_rate");
  const steps = getLatestMetric("steps");
  const bloodPressure = getLatestMetric("blood_pressure");
  const weight = getLatestMetric("weight");

  const handleConnect = async (provider: "apple_health" | "google_fit") => {
    await setupHealthIntegration(provider);
  };

  return (
    <div className="min-h-screen bg-background pb-6">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background border-b">
        <div className="flex items-center justify-between p-4">
          <div>
            <h1 className="text-xl font-semibold">Health Data</h1>
            <p className="text-sm text-muted-foreground">Sync from your devices</p>
          </div>
          <Button variant="ghost" size="icon" onClick={() => setShowPermissions(true)}>
            <Settings className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <div className="p-4 space-y-6">
        {/* Connection Status */}
        <div className="space-y-3">
          <h2 className="font-semibold">Connected Services</h2>
          <ConnectionCard
            provider="apple_health"
            connected={healthIntegration?.provider === "apple_health" && healthIntegration.enabled}
            lastSync={healthIntegration?.lastSyncAt ? format(new Date(healthIntegration.lastSyncAt), "h:mm a") : undefined}
            onConnect={() => handleConnect("apple_health")}
            onDisconnect={() => {}}
            onSync={syncHealthData}
            isSyncing={isHealthSyncing}
          />
          <ConnectionCard
            provider="google_fit"
            connected={healthIntegration?.provider === "google_fit" && healthIntegration.enabled}
            lastSync={healthIntegration?.lastSyncAt ? format(new Date(healthIntegration.lastSyncAt), "h:mm a") : undefined}
            onConnect={() => handleConnect("google_fit")}
            onDisconnect={() => {}}
            onSync={syncHealthData}
            isSyncing={isHealthSyncing}
          />
        </div>

        {/* Privacy Notice */}
        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription className="text-sm">
            Your health data is encrypted and only shared with your healthcare providers with your consent.
          </AlertDescription>
        </Alert>

        {/* Health Metrics */}
        {healthIntegration?.enabled && (
          <>
            <div className="space-y-3">
              <h2 className="font-semibold">Today's Summary</h2>
              <div className="grid grid-cols-2 gap-3">
                {steps && (
                  <HealthMetricCard
                    type="steps"
                    value={steps.value}
                    unit={steps.unit}
                    trend="up"
                    trendValue="+12%"
                    lastUpdated={format(new Date(steps.timestamp), "h:mm a")}
                    goal={10000}
                    current={Number(steps.value)}
                    onClick={() => setSelectedMetric("steps")}
                  />
                )}
                {heartRate && (
                  <HealthMetricCard
                    type="heart_rate"
                    value={heartRate.value}
                    unit={heartRate.unit}
                    trend="stable"
                    trendValue="Normal"
                    lastUpdated={format(new Date(heartRate.timestamp), "h:mm a")}
                    onClick={() => setSelectedMetric("heart_rate")}
                  />
                )}
                {bloodPressure && (
                  <HealthMetricCard
                    type="blood_pressure"
                    value={bloodPressure.value}
                    unit={bloodPressure.unit}
                    trend="down"
                    trendValue="-3%"
                    lastUpdated={format(new Date(bloodPressure.timestamp), "h:mm a")}
                    onClick={() => setSelectedMetric("blood_pressure")}
                  />
                )}
                {weight && (
                  <HealthMetricCard
                    type="weight"
                    value={weight.value}
                    unit={weight.unit}
                    trend="down"
                    trendValue="-2 lbs"
                    lastUpdated={format(new Date(weight.timestamp), "h:mm a")}
                    onClick={() => setSelectedMetric("weight")}
                  />
                )}
              </div>
            </div>

            {/* Weekly Activity */}
            <WeeklyChart data={weeklySteps} goal={10000} unit="steps" />

            {/* Share with Provider */}
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <Smartphone className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Share with Care Team</p>
                    <p className="text-sm text-muted-foreground">
                      Allow your doctors to view your health data
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {/* Empty State */}
        {!healthIntegration?.enabled && (
          <Card>
            <CardContent className="py-12 text-center">
              <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="font-semibold mb-2">Connect Your Health Data</h3>
              <p className="text-sm text-muted-foreground mb-4 max-w-xs mx-auto">
                Link Apple Health or Google Fit to share activity data with your care team
              </p>
              <div className="flex gap-2 justify-center">
                <Button onClick={() => handleConnect("apple_health")}>
                  Connect Apple Health
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Permissions Dialog */}
      <Dialog open={showPermissions} onOpenChange={setShowPermissions}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Data Permissions</DialogTitle>
            <DialogDescription>Choose what health data to sync</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <PermissionToggle
              label="Heart Rate"
              description="Resting and active heart rate"
              enabled={healthIntegration?.permissions.heartRate ?? false}
              onToggle={(enabled) => updateHealthPermissions({ heartRate: enabled })}
              icon={Heart}
            />
            <PermissionToggle
              label="Blood Pressure"
              description="Systolic and diastolic readings"
              enabled={healthIntegration?.permissions.bloodPressure ?? false}
              onToggle={(enabled) => updateHealthPermissions({ bloodPressure: enabled })}
              icon={Activity}
            />
            <PermissionToggle
              label="Steps & Activity"
              description="Daily steps and active minutes"
              enabled={healthIntegration?.permissions.steps ?? false}
              onToggle={(enabled) => updateHealthPermissions({ steps: enabled })}
              icon={Activity}
            />
            <PermissionToggle
              label="Weight"
              description="Body weight measurements"
              enabled={healthIntegration?.permissions.weight ?? false}
              onToggle={(enabled) => updateHealthPermissions({ weight: enabled })}
              icon={Scale}
            />
            <PermissionToggle
              label="Sleep"
              description="Sleep duration and quality"
              enabled={healthIntegration?.permissions.sleep ?? false}
              onToggle={(enabled) => updateHealthPermissions({ sleep: enabled })}
              icon={Moon}
            />
            <PermissionToggle
              label="Blood Glucose"
              description="Blood sugar readings"
              enabled={healthIntegration?.permissions.glucose ?? false}
              onToggle={(enabled) => updateHealthPermissions({ glucose: enabled })}
              icon={Droplet}
            />
          </div>
          <DialogFooter>
            <Button onClick={() => setShowPermissions(false)}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Health Detail Modal */}
      <HealthDetailModal
        open={selectedMetric !== null}
        onOpenChange={(open) => !open && setSelectedMetric(null)}
        type={selectedMetric || ""}
        data={recentHealthData}
      />
    </div>
  );
}

// Compact health widget
export function HealthSummaryWidget() {
  const { recentHealthData, healthIntegration } = useMobileStore();

  if (!healthIntegration?.enabled) {
    return (
      <div className="p-3 bg-muted/50 rounded-lg text-center">
        <Activity className="h-5 w-5 mx-auto text-muted-foreground mb-1" />
        <p className="text-xs text-muted-foreground">Connect health data</p>
      </div>
    );
  }

  const steps = recentHealthData.find(d => d.type === "steps");
  const heartRate = recentHealthData.find(d => d.type === "heart_rate");

  return (
    <div className="flex gap-3">
      {steps && (
        <div className="flex-1 p-2 bg-green-50 rounded-lg">
          <Activity className="h-4 w-4 text-green-600 mb-1" />
          <p className="text-sm font-semibold">{steps.value}</p>
          <p className="text-[10px] text-muted-foreground">steps</p>
        </div>
      )}
      {heartRate && (
        <div className="flex-1 p-2 bg-red-50 rounded-lg">
          <Heart className="h-4 w-4 text-red-500 mb-1" />
          <p className="text-sm font-semibold">{heartRate.value}</p>
          <p className="text-[10px] text-muted-foreground">bpm</p>
        </div>
      )}
    </div>
  );
}

export default HealthIntegrationView;
