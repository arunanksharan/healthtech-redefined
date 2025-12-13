'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  MessageSquare,
  Plus,
  Search,
  Filter,
  Send,
  Mail,
  Phone,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  Calendar,
  MessageCircle,
  Smartphone,
  MoreVertical,
  Reply,
  Archive,
  Trash2,
} from 'lucide-react';
import { communicationsAPI } from '@/lib/api/communications';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { formatSmartDate } from '@/lib/utils/date';
import { cn } from '@/lib/utils/cn';
import toast from 'react-hot-toast';
import { MagicCard } from '@/components/ui/magic-card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// Helper for initials
const getInitials = (name?: string) => {
  if (!name) return '??';
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
};

export default function CommunicationsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [channelFilter, setChannelFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Fetch all communications
  const { data: commsData, isLoading, error } = useQuery({
    queryKey: ['communications', channelFilter, statusFilter],
    queryFn: async () => {
      const [data, error] = await communicationsAPI.getAll({
        channel: channelFilter === 'all' ? undefined : channelFilter,
        status: statusFilter === 'all' ? undefined : statusFilter,
      });
      if (error) throw new Error(error.message);
      return data;
    },
  });

  const communications = commsData?.communications || [];
  const filteredCommunications = communications.filter(comm =>
    searchQuery === '' ||
    comm.patient?.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    comm.message?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    comm.subject?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Auto-select first if none selected and not loading
  if (!selectedId && filteredCommunications.length > 0 && !isLoading) {
    setSelectedId(filteredCommunications[0].id);
  }

  const selectedComm = communications.find(c => c.id === selectedId);

  const stats = {
    total: communications.length,
    whatsapp: communications.filter(c => c.channel === 'whatsapp').length,
    sms: communications.filter(c => c.channel === 'sms').length,
    email: communications.filter(c => c.channel === 'email').length,
    delivered: communications.filter(c => c.status === 'delivered').length,
    pending: communications.filter(c => c.status === 'pending').length,
    failed: communications.filter(c => c.status === 'failed').length,
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'whatsapp': return <MessageCircle className="w-4 h-4" />;
      case 'sms': return <Smartphone className="w-4 h-4" />;
      case 'email': return <Mail className="w-4 h-4" />;
      default: return <MessageSquare className="w-4 h-4" />;
    }
  };

  const getChannelColor = (channel: string) => {
    switch (channel) {
      case 'whatsapp': return 'bg-green-100 text-green-700 border-green-200';
      case 'sms': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'email': return 'bg-purple-100 text-purple-700 border-purple-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'delivered': return <CheckCircle2 className="w-4 h-4 text-green-600" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-600" />;
      case 'pending': return <Clock className="w-4 h-4 text-yellow-600" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-theme(spacing.16))]">
      {/* Sticky Glassmorphic Header */}
      <header className="sticky top-16 z-20 flex items-center justify-between p-6 bg-white/80 backdrop-blur-md border-b border-gray-200/50 supports-[backdrop-filter]:bg-white/60">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Communications</h1>
          <p className="text-sm text-gray-500 mt-1">Manage patient conversations and alerts</p>
        </div>
        <div className="flex gap-3">
          <Button className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-all hover:scale-105">
            <Plus className="w-4 h-4 mr-2" />
            New Message
          </Button>
        </div>
      </header>

      <div className="flex-1 p-6 overflow-hidden flex flex-col gap-6">
        {/* Magic Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 shrink-0">
          <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#eff6ff">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-gray-500">Total Messages</CardTitle>
              <MessageSquare className="w-4 h-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
              <p className="text-xs text-gray-500 mt-1">Across all channels</p>
            </CardContent>
          </MagicCard>

          <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#f0fdf4">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-gray-500">WhatsApp</CardTitle>
              <MessageCircle className="w-4 h-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{stats.whatsapp}</div>
              <div className="flex items-center gap-1 mt-1">
                <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                <p className="text-xs text-gray-500">Active channel</p>
              </div>
            </CardContent>
          </MagicCard>

          <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#eff6ff">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-gray-500">SMS Sent</CardTitle>
              <Smartphone className="w-4 h-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{stats.sms}</div>
              <p className="text-xs text-gray-500 mt-1">High open rate</p>
            </CardContent>
          </MagicCard>

          <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#faf5ff">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-gray-500">Emails</CardTitle>
              <Mail className="w-4 h-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{stats.email}</div>
              <p className="text-xs text-gray-500 mt-1">{stats.delivered} Delivered</p>
            </CardContent>
          </MagicCard>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden flex">
          <ResizablePanelGroup direction="horizontal">
            {/* Thread List - Sidebar */}
            <ResizablePanel defaultSize={35} minSize={25} maxSize={45}>
              <div className="h-full flex flex-col bg-gray-50/50">
                <div className="p-4 border-b border-gray-200 bg-white">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      placeholder="Search..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9 bg-gray-50 border-gray-200 focus:bg-white transition-all"
                    />
                  </div>
                  <div className="flex gap-2 mt-3 overflow-x-auto pb-1 no-scrollbar">
                    <Badge
                      variant={channelFilter === 'all' ? 'default' : 'outline'}
                      className="cursor-pointer whitespace-nowrap"
                      onClick={() => setChannelFilter('all')}
                    >
                      All
                    </Badge>
                    <Badge
                      variant={channelFilter === 'whatsapp' ? 'default' : 'outline'}
                      className="cursor-pointer whitespace-nowrap hover:bg-green-50 hover:text-green-700 hover:border-green-200"
                      onClick={() => setChannelFilter('whatsapp')}
                    >
                      WhatsApp
                    </Badge>
                    <Badge
                      variant={channelFilter === 'sms' ? 'default' : 'outline'}
                      className="cursor-pointer whitespace-nowrap hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200"
                      onClick={() => setChannelFilter('sms')}
                    >
                      SMS
                    </Badge>
                    <Badge
                      variant={channelFilter === 'email' ? 'default' : 'outline'}
                      className="cursor-pointer whitespace-nowrap hover:bg-purple-50 hover:text-purple-700 hover:border-purple-200"
                      onClick={() => setChannelFilter('email')}
                    >
                      Email
                    </Badge>
                  </div>
                </div>

                <ScrollArea className="flex-1">
                  {isLoading ? (
                    <div className="p-8 text-center text-gray-500">Loading conversations...</div>
                  ) : filteredCommunications.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">No messages found.</div>
                  ) : (
                    <div className="flex flex-col">
                      {filteredCommunications.map((comm) => (
                        <button
                          key={comm.id}
                          onClick={() => setSelectedId(comm.id)}
                          className={cn(
                            "w-full text-left p-4 border-b border-gray-100 hover:bg-white transition-all focus:outline-none group relative",
                            selectedId === comm.id ? "bg-white shadow-[inset_3px_0_0_0_#2563eb]" : "bg-transparent"
                          )}
                        >
                          <div className="flex justify-between items-start mb-1">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-gray-900 truncate max-w-[140px]">
                                {comm.patient?.name || 'Unknown'}
                              </span>
                              {selectedId === comm.id && <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />}
                            </div>
                            <span className="text-[10px] text-gray-400 whitespace-nowrap">
                              {formatSmartDate(comm.sent_at || comm.created_at)}
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 line-clamp-2 leading-relaxed group-hover:text-gray-700">
                            {comm.message || comm.body || 'No content'}
                          </p>
                          <div className="flex items-center gap-2 mt-3">
                            <Badge variant="secondary" className={cn("text-[10px] h-5 px-1.5 font-normal bg-white border border-gray-200", getChannelColor(comm.channel))}>
                              {getChannelIcon(comm.channel)}
                              <span className="ml-1 capitalize">{comm.channel}</span>
                            </Badge>
                            {comm.status === 'failed' && (
                              <Badge variant="destructive" className="text-[10px] h-5 px-1.5">Failed</Badge>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </div>
            </ResizablePanel>

            <ResizableHandle />

            {/* Message Detail - Main View */}
            <ResizablePanel defaultSize={65}>
              {selectedComm ? (
                <div className="h-full flex flex-col bg-white">
                  {/* Message Header */}
                  <div className="p-6 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white/95 backdrop-blur z-10">
                    <div className="flex items-center gap-4">
                      <Avatar className="w-12 h-12 border border-gray-100 shadow-sm">
                        <AvatarFallback className="bg-blue-50 text-blue-700 text-lg font-medium">
                          {getInitials(selectedComm.patient?.name)}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <h2 className="text-lg font-bold text-gray-900">{selectedComm.patient?.name}</h2>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <span>Patient ID: #{selectedComm.patient_id?.slice(0, 8)}</span>
                          <span>•</span>
                          <span className="capitalize">{selectedComm.channel} Thread</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="icon" className="text-gray-400 hover:text-gray-600">
                        <Phone className="w-4 h-4" />
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="text-gray-400 hover:text-gray-600">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>View Patient Profile</DropdownMenuItem>
                          <DropdownMenuItem>Mark as Unread</DropdownMenuItem>
                          <DropdownMenuItem className="text-red-600">Delete Conversation</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>

                  {/* Message Content Area */}
                  <ScrollArea className="flex-1 p-6 bg-gradient-to-b from-gray-50/50 to-white">
                    {/* Template / Subject Info */}
                    {(selectedComm.subject || selectedComm.template_id) && (
                      <div className="mb-6 flex justify-center">
                        <div className="bg-gray-100/80 text-gray-500 text-xs px-3 py-1 rounded-full border border-gray-200">
                          {selectedComm.subject ? `Subject: ${selectedComm.subject}` : `Template: ${selectedComm.template_id}`}
                        </div>
                      </div>
                    )}

                    {/* The Message Bubble */}
                    <div className="flex justify-end mb-4">
                      <div className="max-w-[80%]">
                        <div className="bg-blue-600 text-white rounded-2xl rounded-tr-none px-6 py-4 shadow-sm">
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">
                            {selectedComm.message || selectedComm.body}
                          </p>
                        </div>
                        <div className="flex items-center justify-end gap-1.5 mt-2 text-xs text-gray-400">
                          <span>{formatSmartDate(selectedComm.sent_at || selectedComm.created_at)}</span>
                          <span>•</span>
                          <span className="capitalize flex items-center gap-1">
                            {selectedComm.status}
                            {getStatusIcon(selectedComm.status)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </ScrollArea>

                  {/* Reply Input */}
                  <div className="p-4 border-t border-gray-100 bg-white">
                    <div className="flex gap-4 items-end">
                      <div className="flex-1 bg-gray-50 border border-gray-200 rounded-xl focus-within:ring-2 focus-within:ring-blue-100 focus-within:border-blue-400 transition-all">
                        <textarea
                          placeholder="Type a reply..."
                          className="w-full bg-transparent border-none p-3 h-24 resize-none focus:ring-0 text-sm placeholder:text-gray-400"
                        />
                        <div className="flex items-center justify-between px-2 pb-2">
                          <div className="flex gap-1">
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-gray-600">
                              <Plus className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                      <Button className="h-12 w-12 rounded-xl bg-blue-600 hover:bg-blue-700 shadow-sm flex items-center justify-center">
                        <Send className="w-5 h-5 text-white ml-0.5" />
                      </Button>
                    </div>
                    <p className="text-xs text-center text-gray-400 mt-2">
                      Pressing Enter will not send the message
                    </p>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-gray-400 bg-gray-50/30">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                    <MessageSquare className="w-8 h-8 text-gray-300" />
                  </div>
                  <p className="font-medium text-gray-600">No conversation selected</p>
                  <p className="text-sm mt-1">Select a message from the list to view details</p>
                </div>
              )}
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      </div>
    </div>
  );
}
