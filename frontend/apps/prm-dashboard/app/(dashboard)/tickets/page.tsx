'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Ticket as TicketIcon,
  Plus,
  Search,
  Filter,
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  User,
  Calendar,
  MessageSquare,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react';
import { ticketsAPI } from '@/lib/api/tickets';
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

export default function TicketsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const queryClient = useQueryClient();

  // Fetch all tickets
  const { data: ticketsData, isLoading, error } = useQuery({
    queryKey: ['tickets', categoryFilter, statusFilter, priorityFilter],
    queryFn: async () => {
      const [data, error] = await ticketsAPI.getAll({
        category: categoryFilter === 'all' ? undefined : categoryFilter,
        status: statusFilter === 'all' ? undefined : statusFilter,
        priority: priorityFilter === 'all' ? undefined : priorityFilter,
      });
      if (error) throw new Error(error.message);
      return data;
    },
  });

  // Resolve ticket mutation
  const resolveMutation = useMutation({
    mutationFn: async (ticketId: string) => {
      const [data, error] = await ticketsAPI.resolve(ticketId);
      if (error) throw new Error(error.message);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      toast.success('Ticket resolved successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to resolve ticket: ${error.message}`);
    },
  });

  // Close ticket mutation
  const closeMutation = useMutation({
    mutationFn: async (ticketId: string) => {
      const [data, error] = await ticketsAPI.close(ticketId);
      if (error) throw new Error(error.message);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      toast.success('Ticket closed successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to close ticket: ${error.message}`);
    },
  });

  const tickets = ticketsData?.data || [];
  const filteredTickets = tickets.filter(ticket =>
    searchQuery === '' ||
    ticket.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ticket.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ticket.patient?.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const stats = {
    total: tickets.length,
    open: tickets.filter(t => t.status === 'open').length,
    inProgress: tickets.filter(t => t.status === 'in_progress').length,
    resolved: tickets.filter(t => t.status === 'resolved').length,
    closed: tickets.filter(t => t.status === 'closed').length,
    urgent: tickets.filter(t => t.priority === 'urgent').length,
    high: tickets.filter(t => t.priority === 'high').length,
    billing: tickets.filter(t => t.category === 'billing').length,
    appointment: tickets.filter(t => t.category === 'appointment').length,
    medical: tickets.filter(t => t.category === 'medical').length,
    technical: tickets.filter(t => t.category === 'technical').length,
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'billing': return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'appointment': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'medical': return 'bg-red-100 text-red-700 border-red-200';
      case 'technical': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'general': return 'bg-gray-100 text-gray-700 border-gray-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-700 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      case 'low': return 'bg-green-100 text-green-700 border-green-300';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent': return <AlertTriangle className="w-3 h-3" />;
      case 'high': return <TrendingUp className="w-3 h-3" />;
      default: return null;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open': return <AlertCircle className="w-4 h-4 text-blue-600" />;
      case 'in_progress': return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'resolved': return <CheckCircle2 className="w-4 h-4 text-green-600" />;
      case 'closed': return <XCircle className="w-4 h-4 text-gray-600" />;
      default: return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'default';
      case 'in_progress': return 'warning';
      case 'resolved': return 'success';
      case 'closed': return 'secondary';
      default: return 'default';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Support Tickets</h1>
          <p className="text-gray-500 mt-1">Track and manage patient support tickets</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Ticket
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Total Tickets</CardDescription>
              <TicketIcon className="w-4 h-4 text-gray-400" />
            </div>
            <CardTitle className="text-3xl">{stats.total}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Open</CardDescription>
              <AlertCircle className="w-4 h-4 text-blue-600" />
            </div>
            <CardTitle className="text-3xl text-blue-600">{stats.open}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>In Progress</CardDescription>
              <Clock className="w-4 h-4 text-yellow-600" />
            </div>
            <CardTitle className="text-3xl text-yellow-600">{stats.inProgress}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Resolved</CardDescription>
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            </div>
            <CardTitle className="text-3xl text-green-600">{stats.resolved}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Closed</CardDescription>
              <XCircle className="w-4 h-4 text-gray-600" />
            </div>
            <CardTitle className="text-3xl text-gray-600">{stats.closed}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Category & Priority Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">By Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Billing</span>
                </div>
                <span className="text-sm font-medium">{stats.billing}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Appointment</span>
                </div>
                <span className="text-sm font-medium">{stats.appointment}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Medical</span>
                </div>
                <span className="text-sm font-medium">{stats.medical}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Technical</span>
                </div>
                <span className="text-sm font-medium">{stats.technical}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">By Priority</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span className="text-sm text-gray-700">Urgent</span>
                </div>
                <span className="text-sm font-medium text-red-600">{stats.urgent}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-orange-600" />
                  <span className="text-sm text-gray-700">High</span>
                </div>
                <span className="text-sm font-medium text-orange-600">{stats.high}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Medium</span>
                </div>
                <span className="text-sm font-medium">{tickets.filter(t => t.priority === 'medium').length}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Low</span>
                </div>
                <span className="text-sm font-medium">{tickets.filter(t => t.priority === 'low').length}</span>
              </div>
            </div>
          </CardContent>
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
                  placeholder="Search tickets, patients, or descriptions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Categories</option>
              <option value="billing">Billing</option>
              <option value="appointment">Appointment</option>
              <option value="medical">Medical</option>
              <option value="technical">Technical</option>
              <option value="general">General</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Priorities</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Tickets List */}
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
              Error loading tickets: {(error as Error).message}
            </div>
          </CardContent>
        </Card>
      ) : filteredTickets.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-gray-500">
              <TicketIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No tickets found</p>
              {searchQuery && (
                <p className="text-sm mt-2">Try adjusting your search or filters</p>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Tickets</CardTitle>
            <CardDescription>{filteredTickets.length} tickets</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredTickets.map((ticket) => (
                <div
                  key={ticket.id}
                  className="flex items-start gap-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {/* Patient Avatar */}
                  <Avatar className="mt-1">
                    <AvatarFallback>
                      {ticket.patient?.name
                        ?.split(' ')
                        .map((n) => n[0])
                        .join('')
                        .toUpperCase() || '?'}
                    </AvatarFallback>
                  </Avatar>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-gray-900">
                            {ticket.title}
                          </span>
                          <Badge variant="outline" className={cn("text-xs", getCategoryColor(ticket.category))}>
                            {ticket.category}
                          </Badge>
                          <Badge variant="outline" className={cn("text-xs flex items-center gap-1", getPriorityColor(ticket.priority))}>
                            {getPriorityIcon(ticket.priority)}
                            {ticket.priority}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {ticket.patient?.name || 'No patient'}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {formatSmartDate(ticket.created_at)}
                          </span>
                          {ticket.assigned_to && (
                            <span className="text-xs">
                              Assigned to: {ticket.assigned_to}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        {getStatusIcon(ticket.status)}
                        <Badge variant={getStatusColor(ticket.status)}>
                          {ticket.status.replace('_', ' ')}
                        </Badge>
                      </div>
                    </div>

                    {/* Description */}
                    <div className="text-sm text-gray-700 mb-3 line-clamp-2">
                      {ticket.description}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      {ticket.status !== 'resolved' && ticket.status !== 'closed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => resolveMutation.mutate(ticket.id)}
                          disabled={resolveMutation.isPending}
                        >
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                          Resolve
                        </Button>
                      )}
                      {ticket.status !== 'closed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => closeMutation.mutate(ticket.id)}
                          disabled={closeMutation.isPending}
                        >
                          <XCircle className="w-3 h-3 mr-1" />
                          Close
                        </Button>
                      )}
                      <Button variant="ghost" size="sm">
                        <MessageSquare className="w-3 h-3 mr-1" />
                        Comments
                      </Button>
                      <Button variant="ghost" size="sm">
                        View Details
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
