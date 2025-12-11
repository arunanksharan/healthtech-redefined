'use client';

import { useState } from 'react';
import {
  User,
  Bell,
  Lock,
  Globe,
  Palette,
  Shield,
  Smartphone,
  Mail,
  Save,
  Check,
  ChevronRight,
  Monitor,
  Moon,
  Sun,
  Laptop
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { MagicCard } from '@/components/ui/magic-card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { cn } from '@/lib/utils/cn';
import toast from 'react-hot-toast';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsAPI, UserSettings } from '@/lib/api/settings';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('account');
  const queryClient = useQueryClient();

  // Fetch Settings
  const { data: settings, isLoading: isFetching } = useQuery({
    queryKey: ['user-settings'],
    queryFn: async () => {
      const [data, error] = await settingsAPI.getSettings();
      if (error) throw new Error(error.message);
      return data;
    },
  });

  // Local state for editing (initialized with defaults or fetched data)
  const [formData, setFormData] = useState<UserSettings | null>(null);

  // Sync fetched data to local state
  if (settings && !formData) {
    setFormData(settings);
  }

  // Update Settings Mutation
  const mutation = useMutation({
    mutationFn: async (newData: UserSettings) => {
      const [data, error] = await settingsAPI.updateSettings(newData);
      if (error) throw new Error(error.message);
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['user-settings'], data);
      toast.success('Settings saved successfully');
    },
    onError: () => {
      toast.error('Failed to save settings');
    }
  });

  const handleSave = () => {
    if (formData) {
      mutation.mutate(formData);
    }
  };

  if (isFetching || !formData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Helpers to update nested state
  const updateAccount = (field: keyof UserSettings['account'], value: string) => {
    setFormData(prev => prev ? ({
      ...prev,
      account: { ...prev.account, [field]: value }
    }) : null);
  };

  const updateNotification = (field: keyof UserSettings['notifications'], value: boolean) => {
    setFormData(prev => prev ? ({
      ...prev,
      notifications: { ...prev.notifications, [field]: value }
    }) : null);
  };

  const updateTheme = (theme: 'light' | 'dark' | 'system') => {
    setFormData(prev => prev ? ({
      ...prev,
      appearance: { ...prev.appearance, theme }
    }) : null);
  };

  const menuItems = [
    { id: 'account', label: 'Account', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'privacy', label: 'Privacy & Security', icon: Lock },
    { id: 'integrations', label: 'Integrations', icon: Globe },
  ];

  return (
    <div className="flex flex-col min-h-screen bg-muted/40">
      {/* Sticky Header */}
      <header className="sticky top-16 z-20 flex items-center justify-between p-6 bg-background/80 backdrop-blur-md border-b border-border/50 supports-[backdrop-filter]:bg-background/60">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Settings</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your account preferences and application settings</p>
        </div>
        <Button onClick={handleSave} disabled={mutation.isPending} className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm">
          {mutation.isPending ? (
            <>Saving...</>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </header>

      <div className="p-6 max-w-6xl mx-auto w-full">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Navigation */}
          <aside className="w-full lg:w-64 shrink-0">
            <div className="sticky top-40 space-y-1">
              {menuItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200",
                    activeTab === item.id
                      ? "bg-card text-blue-600 shadow-sm ring-1 ring-border"
                      : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                  )}
                >
                  <item.icon className={cn("w-4 h-4", activeTab === item.id ? "text-blue-600" : "text-muted-foreground")} />
                  {item.label}
                  {activeTab === item.id && (
                    <ChevronRight className="w-4 h-4 ml-auto text-blue-400" />
                  )}
                </button>
              ))}
            </div>
          </aside>

          {/* Main Content Area */}
          <div className="flex-1 min-w-0">
            <MagicCard className="bg-card border border-border shadow-sm p-6 md:p-8" gradientColor="#f8fafc">

              {/* Account Settings */}
              {activeTab === 'account' && (
                <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div>
                    <h2 className="text-lg font-semibold text-foreground">Profile Information</h2>
                    <p className="text-sm text-muted-foreground mt-1">Update your photo and personal details.</p>
                  </div>

                  <Separator className="bg-border" />

                  <div className="flex items-center gap-6">
                    <Avatar className="w-20 h-20 border-4 border-muted shadow-sm">
                      <AvatarImage src="/avatars/01.png" />
                      <AvatarFallback className="bg-blue-100 text-blue-600 text-xl font-bold">RS</AvatarFallback>
                    </Avatar>
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">Change Photo</Button>
                        <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-600 hover:bg-red-50/10">Remove</Button>
                      </div>
                      <p className="text-xs text-muted-foreground">JPG, GIF or PNG. 1MB max.</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">First name</Label>
                      <Input
                        id="firstName"
                        value={formData.account.firstName}
                        onChange={(e) => updateAccount('firstName', e.target.value)}
                        className="bg-muted/50 border-border focus:bg-background"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">Last name</Label>
                      <Input
                        id="lastName"
                        value={formData.account.lastName}
                        onChange={(e) => updateAccount('lastName', e.target.value)}
                        className="bg-muted/50 border-border focus:bg-background"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email address</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                          id="email"
                          value={formData.account.email}
                          onChange={(e) => updateAccount('email', e.target.value)}
                          className="pl-9 bg-muted/50 border-border focus:bg-background"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone number</Label>
                      <div className="relative">
                        <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                          id="phone"
                          value={formData.account.phone}
                          onChange={(e) => updateAccount('phone', e.target.value)}
                          className="pl-9 bg-muted/50 border-border focus:bg-background"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Notification Settings */}
              {activeTab === 'notifications' && (
                <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div>
                    <h2 className="text-lg font-semibold text-foreground">Notifications</h2>
                    <p className="text-sm text-muted-foreground mt-1">Configure how you receive alerts.</p>
                  </div>
                  <Separator className="bg-border" />

                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="text-base">Email Notifications</Label>
                        <p className="text-sm text-muted-foreground">Receive daily summaries of patient activity.</p>
                      </div>
                      <Switch
                        checked={formData.notifications.email}
                        onCheckedChange={(c) => updateNotification('email', c)}
                      />
                    </div>
                    <Separator className="bg-border" />
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="text-base">Push Notifications</Label>
                        <p className="text-sm text-muted-foreground">Real-time alerts for critical events.</p>
                      </div>
                      <Switch
                        checked={formData.notifications.push}
                        onCheckedChange={(c) => updateNotification('push', c)}
                      />
                    </div>
                    <Separator className="bg-border" />
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="text-base">SMS Alerts</Label>
                        <p className="text-sm text-muted-foreground">Get text messages for appointment reminders.</p>
                      </div>
                      <Switch
                        checked={formData.notifications.sms}
                        onCheckedChange={(c) => updateNotification('sms', c)}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Appearance Settings */}
              {activeTab === 'appearance' && (
                <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div>
                    <h2 className="text-lg font-semibold text-foreground">Appearance</h2>
                    <p className="text-sm text-muted-foreground mt-1">Customize the look and feel of the dashboard.</p>
                  </div>
                  <Separator className="bg-border" />

                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2 cursor-pointer group" onClick={() => updateTheme('light')}>
                      <div className={cn(
                        "h-32 rounded-lg border-2 p-2 shadow-sm flex items-center justify-center transition-all",
                        formData.appearance.theme === 'light' ? "border-blue-600 bg-blue-50/50" : "border-border hover:border-blue-300 bg-card"
                      )}>
                        <div className="space-y-2 w-full max-w-[80%]">
                          <div className="h-2 w-full bg-muted rounded-full" />
                          <div className="h-2 w-2/3 bg-muted rounded-full" />
                        </div>
                      </div>
                      <span className={cn(
                        "block text-center text-sm font-medium",
                        formData.appearance.theme === 'light' ? "text-blue-600" : "text-muted-foreground"
                      )}>Light</span>
                    </div>

                    <div className="space-y-2 cursor-pointer group" onClick={() => updateTheme('dark')}>
                      <div className={cn(
                        "h-32 rounded-lg border-2 p-2 flex items-center justify-center transition-all bg-gray-950",
                        formData.appearance.theme === 'dark' ? "border-blue-600" : "border-border hover:border-blue-300"
                      )}>
                        <div className="space-y-2 w-full max-w-[80%]">
                          <div className="h-2 w-full bg-gray-800 rounded-full" />
                          <div className="h-2 w-2/3 bg-gray-800 rounded-full" />
                        </div>
                      </div>
                      <span className={cn(
                        "block text-center text-sm font-medium",
                        formData.appearance.theme === 'dark' ? "text-blue-600" : "text-muted-foreground"
                      )}>Dark</span>
                    </div>

                    <div className="space-y-2 cursor-pointer group" onClick={() => updateTheme('system')}>
                      <div className={cn(
                        "h-32 rounded-lg border-2 p-2 flex items-center justify-center transition-all relative overflow-hidden",
                        formData.appearance.theme === 'system' ? "border-blue-600 bg-blue-50/10" : "border-border hover:border-blue-300 bg-card"
                      )}>
                        <div className="absolute inset-0 bg-gradient-to-br from-gray-100 to-gray-900 opacity-20" />
                        <div className="z-10 text-muted-foreground">
                          <Monitor className="w-8 h-8" />
                        </div>
                      </div>
                      <span className={cn(
                        "block text-center text-sm font-medium",
                        formData.appearance.theme === 'system' ? "text-blue-600" : "text-muted-foreground"
                      )}>System</span>
                    </div>
                  </div>
                </div>
              )}
            </MagicCard>
          </div>
        </div>
      </div>
    </div>
  );
}
