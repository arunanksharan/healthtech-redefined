'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Ticket,
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
  MoreVertical,
  ArrowUpRight,
} from 'lucide-react';
import { ticketsAPI } from '@/lib/api/tickets';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { formatSmartDate } from '@/lib/utils/date';
import { cn } from '@/lib/utils/cn';
import { Skeleton, ListSkeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { MagicCard } from '@/components/ui/magic-card';
import { NumberTicker } from '@/components/ui/number-ticker';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

import { CreateTicketDialog } from '@/components/tickets/create-ticket-dialog';
import { TicketDetailSheet } from '@/components/tickets/ticket-detail-sheet';

export default function TicketsPage() {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [isDetailSheetOpen, setIsDetailSheetOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch all tickets
  const { data: ticketsData, isLoading, isError, error, refetch } = useQuery({
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

  // Fetch ticket stats
  const { data: statsData } = useQuery({
    queryKey: ['tickets-stats'],
    queryFn: async () => {
      const [data, error] = await ticketsAPI.getStats();
      if (error) return null;
      return data;
    },
    refetchInterval: 30000,
  });

  const resolveMutation = useMutation({
    mutationFn: async (ticketId: string) => {
      const [data, error] = await ticketsAPI.resolve(ticketId);
      if (error) throw new Error(error.message);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      toast({ title: 'Success', description: 'Ticket resolved successfully', variant: 'default' });
    },
    onError: (error: Error) => toast({ title: 'Error', description: `Failed: ${error.message}`, variant: 'destructive' }),
  });

  const closeMutation = useMutation({
    mutationFn: async (ticketId: string) => {
      const [data, error] = await ticketsAPI.close(ticketId);
      if (error) throw new Error(error.message);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      toast({ title: 'Success', description: 'Ticket closed', variant: 'default' });
    },
    onError: (error: Error) => toast({ title: 'Error', description: `Failed: ${error.message}`, variant: 'destructive' }),
  });

  const tickets = ticketsData?.tickets || [];
  const filteredTickets = tickets.filter(ticket =>
    searchQuery === '' ||
    ticket.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ticket.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ticket.patient?.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const stats = {
    total: statsData?.total || 0,
    open: statsData?.open || 0,
    inProgress: statsData?.in_progress || 0,
    resolved: statsData?.resolved || 0,
    urgent: statsData?.urgent || 0,
  };

  const getPriorityInfo = (priority: string) => {
    switch (priority) {
      case 'urgent': return { color: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800', icon: AlertTriangle, label: 'Urgent' };
      case 'high': return { color: 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800', icon: TrendingUp, label: 'High' };
      case 'medium': return { color: 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800', icon: AlertCircle, label: 'Medium' };
      default: return { color: 'text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-700', icon: CheckCircle2, label: 'Low' };
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300';
      case 'in_progress': return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300';
      case 'resolved': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300';
      case 'closed': return 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400';
      default: return 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400';
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-muted/40">
      {/* Sticky Header */}
      <header className="sticky top-0 z-30 flex items-center justify-between p-6 bg-background/80 backdrop-blur-md border-b border-border/50 supports-[backdrop-filter]:bg-background/60">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Support Tickets</h1>
          <p className="text-sm text-muted-foreground mt-1">Track and resolve patient inquiries</p>
        </div>
        <Button
          onClick={() => setIsCreateDialogOpen(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Ticket
        </Button>
      </header>

      <div className="p-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--info) / 0.15)">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Tickets</CardTitle>
              <Ticket className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                <NumberTicker value={stats.total} />
              </div>
            </CardContent>
          </MagicCard>
          <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--destructive) / 0.15)">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">Urgent</CardTitle>
              <AlertTriangle className="w-4 h-4 text-red-500 dark:text-red-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                <NumberTicker value={stats.urgent} />
              </div>
              <div className="mt-1 text-xs text-red-600 dark:text-red-400 font-medium">Needs attention</div>
            </CardContent>
          </MagicCard>
          <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--success) / 0.15)">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">Resolved</CardTitle>
              <CheckCircle2 className="w-4 h-4 text-green-500 dark:text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                <NumberTicker value={stats.resolved} />
              </div>
            </CardContent>
          </MagicCard>
          <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--warning) / 0.15)">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">In Progress</CardTitle>
              <Clock className="w-4 h-4 text-amber-500 dark:text-amber-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                <NumberTicker value={stats.inProgress} />
              </div>
            </CardContent>
          </MagicCard>
        </div>

        {/* Filters */}
        <div className="bg-card p-4 rounded-xl border border-border shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search by title, ID or patient..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-muted/50 border-border focus:bg-background"
            />
          </div>
          <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-3 py-2 text-sm bg-muted/50 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-foreground"
            >
              <option value="all">Category: All</option>
              <option value="billing">Billing</option>
              <option value="medical">Medical</option>
              <option value="technical">Technical</option>
            </select>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="px-3 py-2 text-sm bg-muted/50 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-foreground"
            >
              <option value="all">Priority: All</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
            </select>
          </div>
        </div>

        {/* Ticket List */}
        {isLoading ? (
          <ListSkeleton items={5} />
        ) : isError ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error Loading Tickets</AlertTitle>
            <AlertDescription>{(error as Error)?.message}</AlertDescription>
          </Alert>
        ) : filteredTickets.length === 0 ? (
          <div className="text-center py-12 bg-card rounded-xl border border-border border-dashed">
            <Ticket className="w-12 h-12 mx-auto mb-3 text-muted" />
            <h3 className="text-lg font-medium text-foreground">No tickets found</h3>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTickets.map((ticket) => {
              const priorityInfo = getPriorityInfo(ticket.priority);
              const PriorityIcon = priorityInfo.icon;

              return (
                <div key={ticket.id} className="group bg-card rounded-xl border border-border p-4 hover:border-blue-300 hover:shadow-md transition-all duration-200 flex flex-col md:flex-row gap-4 items-start md:items-center">
                  {/* Priority Indicator */}
                  <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center shrink-0", priorityInfo.color)}>
                    <PriorityIcon className="w-5 h-5" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-1">
                      <h3 className="text-base font-semibold text-foreground truncate group-hover:text-blue-600 transition-colors">
                        {ticket.title}
                      </h3>

                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-1 mb-2">{ticket.description}</p>

                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-muted-foreground" />
                        <span className="font-medium text-foreground/80">{ticket.patient?.name || 'Start New'}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-muted-foreground" />
                        <span>{formatSmartDate(ticket.created_at)}</span>
                      </div>
                      <Badge variant="secondary" className={cn("capitalize text-[10px] h-5 px-1.5 font-normal", getStatusColor(ticket.status))}>
                        {ticket.status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 w-full md:w-auto border-t md:border-t-0 border-border/50 pt-3 md:pt-0 mt-2 md:mt-0">
                    {ticket.status !== 'resolved' && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 md:flex-none text-xs h-8"
                        onClick={() => resolveMutation.mutate(ticket.id)}
                      >
                        Resolve
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 px-2"
                      onClick={() => {
                        setSelectedTicketId(ticket.id);
                        setIsDetailSheetOpen(true);
                      }}
                    >
                      <MessageSquare className="w-4 h-4 text-muted-foreground" />
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <MoreVertical className="w-4 h-4 text-muted-foreground" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => {
                          setSelectedTicketId(ticket.id);
                          setIsDetailSheetOpen(true);
                        }}>View Details</DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600" onClick={() => closeMutation.mutate(ticket.id)}>
                          Close Ticket
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <CreateTicketDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onSuccess={() => refetch()}
      />

      <TicketDetailSheet
        ticketId={selectedTicketId}
        open={isDetailSheetOpen}
        onOpenChange={setIsDetailSheetOpen}
      />
    </div>
  );
}
