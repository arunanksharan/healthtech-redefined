'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
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

import {
    useRoomMessages,
    useTypingIndicator,
    usePresence
} from '@/lib/hooks/useWebSocket';
import { CreateMessageDialog } from '@/components/communications/create-message-dialog';

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
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
    const [replyMessage, setReplyMessage] = useState('');
    const [isSendingReply, setIsSendingReply] = useState(false);

    // WebSocket Integration
    const conversationId = selectedId || '';
    /*
    const {
        messages: realTimeMessages,
        sendMessage: sendRealTimeMessage
    } = useRoomMessages(conversationId);
    */
    const realTimeMessages: any[] = [];
    const sendRealTimeMessage = async () => { };

    /*
    const {
        typingUsers,
        startTyping,
        stopTyping
    } = useTypingIndicator(conversationId);
    */
    const typingUsers: string[] = [];
    const startTyping = () => { };
    const stopTyping = () => { };

    // Track presence of the selected patient (if we had their generic user ID)
    // const presence = usePresence(selectedComm?.patient_id ? [selectedComm.patient_id] : []);

    // Combine historical and real-time messages (simplified for demo)
    // In a real app, you'd merge `commsData` history with `realTimeMessages`


    // Fetch all communications
    const { data: commsData, isLoading, error, refetch } = useQuery({
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

    console.log('[CommunicationsPage] Render. selectedId:', selectedId, 'conversationId:', conversationId, 'isLoading:', isLoading, 'commsLength:', commsData?.communications?.length);

    // Fetch stats separately
    const { data: statsData } = useQuery({
        queryKey: ['communications-stats'],
        queryFn: async () => {
            const [data, error] = await communicationsAPI.getStats();
            if (error) return null;
            return data;
        },
        // Refresh stats every minute
        refetchInterval: 60000,
    });

    const deleteMutation = useMutation({
        mutationFn: async (id: string) => {
            const [_, error] = await communicationsAPI.delete(id);
            if (error) throw new Error(error.message);
            return id;
        },
        onSuccess: (deletedId) => {
            toast.success('Conversation deleted');
            if (selectedId === deletedId) {
                setSelectedId(null);
            }
            refetch();
        },
        onError: (error) => {
            toast.error(`Failed to delete: ${error.message}`);
        },
    });

    const handleReply = async () => {
        if (!selectedComm || !replyMessage.trim()) return;

        setIsSendingReply(true);
        try {
            let error = null;
            if (selectedComm.channel === 'whatsapp') {
                [_, error] = await communicationsAPI.sendWhatsApp({
                    patient_id: selectedComm.patient_id,
                    message: replyMessage,
                });
            } else if (selectedComm.channel === 'sms') {
                [_, error] = await communicationsAPI.sendSMS({
                    patient_id: selectedComm.patient_id,
                    message: replyMessage,
                });
            } else {
                [_, error] = await communicationsAPI.sendEmail({
                    patient_id: selectedComm.patient_id,
                    subject: `Re: ${selectedComm.subject || 'Message'}`,
                    body: replyMessage,
                });
            }

            if (error) throw new Error(error.message);

            toast.success('Reply sent');
            setReplyMessage('');
            refetch();
        } catch (err: any) {
            toast.error(err.message || 'Failed to send reply');
        } finally {
            setIsSendingReply(false);
        }
    };

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
        total: statsData?.total || 0,
        whatsapp: statsData?.whatsapp || 0,
        sms: statsData?.sms || 0,
        email: statsData?.email || 0,
        delivered: statsData?.delivered || 0,
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
            case 'whatsapp': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800';
            case 'sms': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800';
            case 'email': return 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800';
            default: return 'bg-muted text-muted-foreground border-border';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'delivered': return <CheckCircle2 className="w-4 h-4 text-green-600" />;
            case 'failed': return <XCircle className="w-4 h-4 text-red-600" />;
            case 'pending': return <Clock className="w-4 h-4 text-yellow-600" />;
            default: return <Clock className="w-4 h-4 text-muted-foreground" />;
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-theme(spacing.16))]">
            {/* Sticky Glassmorphic Header */}
            <header className="sticky top-0 z-30 flex items-center justify-between p-6 bg-background/80 backdrop-blur-md border-b border-border/50 supports-[backdrop-filter]:bg-background/60">
                <div>
                    <h1 className="text-2xl font-bold text-foreground tracking-tight">Communications</h1>
                    <p className="text-sm text-muted-foreground mt-1">Manage patient conversations and alerts</p>
                </div>
                <div className="flex gap-3">
                    <Button
                        onClick={() => setIsCreateDialogOpen(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-all hover:scale-105"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        New Message
                    </Button>
                </div>
            </header>

            <div className="flex-1 p-6 overflow-hidden flex flex-col gap-6">
                {/* Magic Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 shrink-0">
                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--info) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Total Messages</CardTitle>
                            <MessageSquare className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">{stats.total}</div>
                            <p className="text-xs text-muted-foreground mt-1">Across all channels</p>
                        </CardContent>
                    </MagicCard>

                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--success) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">WhatsApp</CardTitle>
                            <MessageCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">{stats.whatsapp}</div>
                            <div className="flex items-center gap-1 mt-1">
                                <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                                <p className="text-xs text-muted-foreground">Active channel</p>
                            </div>
                        </CardContent>
                    </MagicCard>

                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--info) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">SMS Sent</CardTitle>
                            <Smartphone className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">{stats.sms}</div>
                            <p className="text-xs text-muted-foreground mt-1">High open rate</p>
                        </CardContent>
                    </MagicCard>

                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--primary) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Emails</CardTitle>
                            <Mail className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">{stats.email}</div>
                            <p className="text-xs text-muted-foreground mt-1">{stats.delivered} Delivered</p>
                        </CardContent>
                    </MagicCard>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 bg-card border border-border rounded-xl shadow-sm overflow-hidden flex">
                    <ResizablePanelGroup direction="horizontal">
                        {/* Thread List - Sidebar */}
                        <ResizablePanel defaultSize={35} minSize={25} maxSize={45}>
                            <div className="h-full flex flex-col bg-muted/30">
                                <div className="p-4 border-b border-border bg-card">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                        <Input
                                            placeholder="Search..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="pl-9 bg-muted/50 border-border focus:bg-background transition-all"
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
                                            className="cursor-pointer whitespace-nowrap hover:bg-green-50 hover:text-green-700 hover:border-green-200 dark:hover:bg-green-900/30 dark:hover:text-green-300 dark:hover:border-green-800"
                                            onClick={() => setChannelFilter('whatsapp')}
                                        >
                                            WhatsApp
                                        </Badge>
                                        <Badge
                                            variant={channelFilter === 'sms' ? 'default' : 'outline'}
                                            className="cursor-pointer whitespace-nowrap hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 dark:hover:bg-blue-900/30 dark:hover:text-blue-300 dark:hover:border-blue-800"
                                            onClick={() => setChannelFilter('sms')}
                                        >
                                            SMS
                                        </Badge>
                                        <Badge
                                            variant={channelFilter === 'email' ? 'default' : 'outline'}
                                            className="cursor-pointer whitespace-nowrap hover:bg-purple-50 hover:text-purple-700 hover:border-purple-200 dark:hover:bg-purple-900/30 dark:hover:text-purple-300 dark:hover:border-purple-800"
                                            onClick={() => setChannelFilter('email')}
                                        >
                                            Email
                                        </Badge>
                                    </div>
                                </div>

                                <ScrollArea className="flex-1">
                                    {isLoading ? (
                                        <div className="p-8 text-center text-muted-foreground">Loading conversations...</div>
                                    ) : filteredCommunications.length === 0 ? (
                                        <div className="p-8 text-center text-muted-foreground">No messages found.</div>
                                    ) : (
                                        <div className="flex flex-col">
                                            {filteredCommunications.map((comm) => (
                                                <button
                                                    key={comm.id}
                                                    onClick={() => setSelectedId(comm.id)}
                                                    className={cn(
                                                        "w-full text-left p-4 border-b border-border hover:bg-muted/50 transition-all focus:outline-none group relative",
                                                        selectedId === comm.id ? "bg-card shadow-[inset_3px_0_0_0_#2563eb]" : "bg-transparent"
                                                    )}
                                                >
                                                    <div className="flex justify-between items-start mb-1">
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-semibold text-foreground truncate max-w-[140px]">
                                                                {comm.patient?.name || 'Unknown'}
                                                            </span>
                                                            {selectedId === comm.id && <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />}
                                                        </div>
                                                        <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                                                            {formatSmartDate(comm.sent_at || comm.created_at)}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed group-hover:text-foreground">
                                                        {comm.message || comm.body || 'No content'}
                                                    </p>
                                                    <div className="flex items-center gap-2 mt-3">
                                                        <Badge variant="secondary" className={cn("text-[10px] h-5 px-1.5 font-normal border border-border", getChannelColor(comm.channel))}>
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
                                <div className="h-full flex flex-col bg-card">
                                    {/* Message Header */}
                                    <div className="p-6 border-b border-border flex items-center justify-between sticky top-0 bg-card/95 backdrop-blur z-10">
                                        <div className="flex items-center gap-4">
                                            <Avatar className="w-12 h-12 border border-border shadow-sm">
                                                <AvatarFallback className="bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-lg font-medium">
                                                    {getInitials(selectedComm.patient?.name)}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div>
                                                <h2 className="text-lg font-bold text-foreground">{selectedComm.patient?.name}</h2>
                                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                    <span>Patient ID: #{selectedComm.patient_id?.slice(0, 8)}</span>
                                                    <span>•</span>
                                                    <span className="capitalize">{selectedComm.channel} Thread</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
                                                <Phone className="w-4 h-4" />
                                            </Button>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
                                                        <MoreVertical className="w-4 h-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem>View Patient Profile</DropdownMenuItem>
                                                    <DropdownMenuItem>Mark as Unread</DropdownMenuItem>
                                                    <DropdownMenuItem
                                                        className="text-red-600 focus:text-red-700 focus:bg-red-50 dark:focus:bg-red-900/20"
                                                        onClick={() => {
                                                            if (confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
                                                                deleteMutation.mutate(selectedComm.id);
                                                            }
                                                        }}
                                                    >
                                                        Delete Conversation
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </div>
                                    </div>

                                    {/* Message Content Area */}
                                    <ScrollArea className="flex-1 p-6 bg-gradient-to-b from-muted/30 to-card">
                                        {/* Template / Subject Info */}
                                        {(selectedComm.subject || selectedComm.template_id) && (
                                            <div className="mb-6 flex justify-center">
                                                <div className="bg-muted text-muted-foreground text-xs px-3 py-1 rounded-full border border-border">
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
                                                <div className="flex items-center justify-end gap-1.5 mt-2 text-xs text-muted-foreground">
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
                                    <div className="p-4 border-t border-border bg-card">
                                        <div className="flex flex-col gap-2">
                                            <div className="flex gap-2 items-end">
                                                <div className="flex-1">
                                                    <Input
                                                        placeholder="Type your reply..."
                                                        value={replyMessage}
                                                        onChange={(e) => setReplyMessage(e.target.value)}
                                                        onFocus={() => startTyping()}
                                                        onBlur={() => stopTyping()}
                                                        onKeyDown={(e) => {
                                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                                handleReply();
                                                            }
                                                        }}
                                                    />
                                                </div>
                                                <Button
                                                    onClick={handleReply}
                                                    disabled={!replyMessage.trim() || isSendingReply}
                                                >
                                                    {isSendingReply ? (
                                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                                                    ) : (
                                                        <Send className="h-4 w-4" />
                                                    )}
                                                </Button>
                                            </div>

                                            <div className="flex justify-between items-center px-1">
                                                <div className="h-4">
                                                    {typingUsers.length > 0 && (
                                                        <p className="text-xs text-blue-600 animate-pulse font-medium">
                                                            {typingUsers.length > 1
                                                                ? `${typingUsers.length} people are typing...`
                                                                : "Someone is typing..."}
                                                        </p>
                                                    )}
                                                </div>
                                                <p className="text-[10px] text-muted-foreground">
                                                    Press Enter to send
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-muted-foreground bg-muted/20">
                                    <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                                        <MessageSquare className="w-8 h-8 text-muted-foreground" />
                                    </div>
                                    <p className="font-medium text-muted-foreground">No conversation selected</p>
                                    <p className="text-sm mt-1">Select a message from the list to view details</p>
                                </div>
                            )}
                        </ResizablePanel>
                    </ResizablePanelGroup>
                </div>
            </div>

            <CreateMessageDialog
                open={isCreateDialogOpen}
                onOpenChange={setIsCreateDialogOpen}
                onSuccess={() => refetch()}
            />
        </div >
    );
}
