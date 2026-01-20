"use client";

import { useEffect, useState } from "react";
import {
  Settings2,
  Globe,
  Webhook,
  Shield,
  Server,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Plus,
  Trash2,
  Edit,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  zoiceHealthAPI,
  zoiceWebhooksAPI,
  zoiceProviderConfigsAPI,
} from "@/lib/api/zoice";

interface WebhookConfig {
  id: string;
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
}

interface ProviderConfig {
  id: string;
  name: string;
  service_type: "stt" | "tts" | "llm" | "vad" | "realtime_audio";
  provider: string;
  is_default: boolean;
}

export default function ZoiceSettingsPage() {
  const [healthStatus, setHealthStatus] = useState<{
    status: "connected" | "error" | "loading";
    message?: string;
  }>({ status: "loading" });
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([]);
  const [providerConfigs, setProviderConfigs] = useState<ProviderConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setIsLoading(true);

    // Fetch health status
    try {
      const [health, healthError] = await zoiceHealthAPI.check();
      if (healthError) {
        setHealthStatus({ status: "error", message: healthError.message });
      } else if (health) {
        setHealthStatus({
          status: health.status,
          message: health.status === "connected" ? "Zoice backend is healthy" : health.error,
        });
      }
    } catch (err) {
      setHealthStatus({ status: "error", message: "Failed to check health" });
    }

    // Fetch webhooks
    try {
      const [webhooksData, webhooksError] = await zoiceWebhooksAPI.getAll();
      if (!webhooksError && webhooksData) {
        setWebhooks(webhooksData);
      }
    } catch (err) {
      console.error("Failed to fetch webhooks:", err);
    }

    // Fetch provider configs
    try {
      const [configs, configsError] = await zoiceProviderConfigsAPI.getAll();
      if (!configsError && configs) {
        setProviderConfigs(configs);
      }
    } catch (err) {
      console.error("Failed to fetch provider configs:", err);
    }

    setIsLoading(false);
  };

  const handleWebhookToggle = async (webhook: WebhookConfig) => {
    try {
      await zoiceWebhooksAPI.update(webhook.id, { is_active: !webhook.is_active });
      setWebhooks((prev) =>
        prev.map((w) => (w.id === webhook.id ? { ...w, is_active: !w.is_active } : w))
      );
    } catch (err) {
      console.error("Failed to toggle webhook:", err);
    }
  };

  const handleDeleteWebhook = async (webhookId: string) => {
    if (!confirm("Are you sure you want to delete this webhook?")) return;
    try {
      await zoiceWebhooksAPI.delete(webhookId);
      setWebhooks((prev) => prev.filter((w) => w.id !== webhookId));
    } catch (err) {
      console.error("Failed to delete webhook:", err);
    }
  };

  const serviceTypeLabels: Record<string, { label: string; color: string }> = {
    stt: { label: "Speech-to-Text", color: "bg-blue-500" },
    tts: { label: "Text-to-Speech", color: "bg-green-500" },
    llm: { label: "Language Model", color: "bg-purple-500" },
    vad: { label: "Voice Activity", color: "bg-yellow-500" },
    realtime_audio: { label: "Realtime Audio", color: "bg-orange-500" },
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Zoice Settings</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Configure Zoice voice AI integration settings
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchSettings} disabled={isLoading}>
          <RefreshCw className={cn("w-4 h-4 mr-2", isLoading && "animate-spin")} />
          Refresh
        </Button>
      </div>

      {/* Health Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            Connection Status
          </CardTitle>
          <CardDescription>Zoice backend service health</CardDescription>
        </CardHeader>
        <CardContent>
          {healthStatus.status === "loading" ? (
            <div className="flex items-center gap-3">
              <Skeleton className="w-6 h-6 rounded-full" />
              <Skeleton className="h-4 w-32" />
            </div>
          ) : (
            <div className="flex items-center gap-3">
              {healthStatus.status === "connected" ? (
                <>
                  <div className="p-1.5 bg-green-100 dark:bg-green-900/30 rounded-full">
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                  </div>
                  <div>
                    <p className="font-medium text-green-600 dark:text-green-400">Connected</p>
                    <p className="text-sm text-gray-500">{healthStatus.message}</p>
                  </div>
                </>
              ) : (
                <>
                  <div className="p-1.5 bg-red-100 dark:bg-red-900/30 rounded-full">
                    <XCircle className="w-5 h-5 text-red-500" />
                  </div>
                  <div>
                    <p className="font-medium text-red-600 dark:text-red-400">Connection Error</p>
                    <p className="text-sm text-gray-500">{healthStatus.message}</p>
                  </div>
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Webhooks */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Webhook className="w-5 h-5" />
                Webhooks
              </CardTitle>
              <CardDescription>Configure webhook endpoints for call events</CardDescription>
            </div>
            <Button size="sm" className="bg-purple-500 hover:bg-purple-600">
              <Plus className="w-4 h-4 mr-2" />
              Add Webhook
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-48" />
                  </div>
                  <Skeleton className="h-6 w-12" />
                </div>
              ))}
            </div>
          ) : webhooks.length === 0 ? (
            <div className="text-center py-8">
              <Webhook className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No webhooks configured</p>
              <p className="text-sm text-gray-400 mt-1">Add a webhook to receive call event notifications</p>
            </div>
          ) : (
            <div className="space-y-3">
              {webhooks.map((webhook) => (
                <div
                  key={webhook.id}
                  className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-gray-900 dark:text-white">{webhook.name}</p>
                      <Badge variant={webhook.is_active ? "default" : "secondary"} className="text-xs">
                        {webhook.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-500 font-mono mt-1">{webhook.url}</p>
                    <div className="flex gap-1 mt-2">
                      {webhook.events.map((event) => (
                        <Badge key={event} variant="outline" className="text-xs">
                          {event}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={webhook.is_active}
                      onCheckedChange={() => handleWebhookToggle(webhook)}
                    />
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-red-500 hover:text-red-600"
                      onClick={() => handleDeleteWebhook(webhook.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Provider Configurations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5" />
            Provider Configurations
          </CardTitle>
          <CardDescription>Manage AI service providers (STT, TTS, LLM)</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="p-4 border rounded-lg">
                  <Skeleton className="h-4 w-24 mb-2" />
                  <Skeleton className="h-3 w-32" />
                </div>
              ))}
            </div>
          ) : providerConfigs.length === 0 ? (
            <div className="text-center py-8">
              <Globe className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No provider configurations found</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {providerConfigs.map((config) => {
                const typeConfig = serviceTypeLabels[config.service_type] || {
                  label: config.service_type,
                  color: "bg-gray-500",
                };
                return (
                  <div
                    key={config.id}
                    className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <Badge className={cn("text-xs text-white mb-2", typeConfig.color)}>
                          {typeConfig.label}
                        </Badge>
                        <p className="font-medium text-gray-900 dark:text-white">{config.name}</p>
                        <p className="text-sm text-gray-500 mt-1">Provider: {config.provider}</p>
                      </div>
                      {config.is_default && (
                        <Badge variant="outline" className="text-xs">
                          Default
                        </Badge>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            API Configuration
          </CardTitle>
          <CardDescription>Zoice API connection settings (managed by PRM backend)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-gray-500">API Endpoint</Label>
                <div className="flex items-center gap-2 mt-1">
                  <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-md text-sm font-mono">
                    /api/v1/prm/admin/zoice
                  </code>
                  <Button variant="ghost" size="sm">
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              <div>
                <Label className="text-gray-500">Authentication</Label>
                <p className="mt-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-md text-sm">
                  API Key (configured in PRM backend)
                </p>
              </div>
            </div>
            <p className="text-sm text-gray-500">
              The Zoice integration is proxied through the PRM backend for security. API keys are managed
              in the backend environment configuration.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
