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
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { formatSmartDate } from '@/lib/utils/date';
import { cn } from '@/lib/utils/cn';
import toast from 'react-hot-toast';

export default function CommunicationsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [channelFilter, setChannelFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

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

  const communications = commsData?.items || [];
  const filteredCommunications = communications.filter(comm =>
    searchQuery === '' ||
    comm.patient?.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    comm.message?.toLowerCase().includes(searchQuery.toLowerCase())
  );

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered': return 'success';
      case 'failed': return 'destructive';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Communications</h1>
          <p className="text-gray-500 mt-1">Manage patient communications across all channels</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Message
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Total Messages</CardDescription>
              <MessageSquare className="w-4 h-4 text-gray-400" />
            </div>
            <CardTitle className="text-3xl">{stats.total}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Delivered</CardDescription>
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            </div>
            <CardTitle className="text-3xl text-green-600">{stats.delivered}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Pending</CardDescription>
              <Clock className="w-4 h-4 text-yellow-600" />
            </div>
            <CardTitle className="text-3xl text-yellow-600">{stats.pending}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Failed</CardDescription>
              <XCircle className="w-4 h-4 text-red-600" />
            </div>
            <CardTitle className="text-3xl text-red-600">{stats.failed}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Channel Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <MessageCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <CardDescription>WhatsApp</CardDescription>
                <CardTitle className="text-2xl">{stats.whatsapp}</CardTitle>
              </div>
            </div>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <Smartphone className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <CardDescription>SMS</CardDescription>
                <CardTitle className="text-2xl">{stats.sms}</CardTitle>
              </div>
            </div>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <Mail className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <CardDescription>Email</CardDescription>
                <CardTitle className="text-2xl">{stats.email}</CardTitle>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* Search & Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search messages or patients..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={channelFilter}
              onChange={(e) => setChannelFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Channels</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="sms">SMS</option>
              <option value="email">Email</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="delivered">Delivered</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
            </select>
            <Button variant="outline">
              <Filter className="w-4 h-4 mr-2" />
              More
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Communications List */}
      {isLoading ? (
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-red-600">
              Error loading communications: {(error as Error).message}
            </div>
          </CardContent>
        </Card>
      ) : filteredCommunications.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-gray-500">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No communications found</p>
              {searchQuery && (
                <p className="text-sm mt-2">Try adjusting your search or filters</p>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Communication History</CardTitle>
            <CardDescription>{filteredCommunications.length} messages</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredCommunications.map((comm) => (
                <div
                  key={comm.id}
                  className="flex items-start gap-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {/* Patient Avatar */}
                  <Avatar className="mt-1">
                    <AvatarFallback>
                      {comm.patient?.name
                        ?.split(' ')
                        .map((n) => n[0])
                        .join('')
                        .toUpperCase() || '?'}
                    </AvatarFallback>
                  </Avatar>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {comm.patient?.name || 'Unknown Patient'}
                          </span>
                          <Badge variant="outline" className={cn("text-xs", getChannelColor(comm.channel))}>
                            <span className="mr-1">{getChannelIcon(comm.channel)}</span>
                            {comm.channel}
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-500 mt-1">
                          {formatSmartDate(comm.sent_at || comm.created_at)}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(comm.status)}
                        <Badge variant={getStatusColor(comm.status)}>
                          {comm.status}
                        </Badge>
                      </div>
                    </div>

                    {/* Message Preview */}
                    <div className="text-sm text-gray-700">
                      {comm.channel === 'email' && comm.subject && (
                        <div className="font-medium mb-1">
                          Subject: {comm.subject}
                        </div>
                      )}
                      <div className="line-clamp-2">
                        {comm.message || comm.body || 'No message content'}
                      </div>
                    </div>

                    {/* Metadata */}
                    {comm.template_id && (
                      <div className="mt-2 text-xs text-gray-500">
                        Template: {comm.template_id}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <Button variant="ghost" size="sm">
                    View Details
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
