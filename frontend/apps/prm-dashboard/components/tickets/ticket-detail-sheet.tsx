'use client';

import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ticket, TicketComment } from '@/lib/api/types';
import { ticketsAPI } from '@/lib/api/tickets';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
    Send,
    User,
    Clock,
    AlertCircle,
    CheckCircle2,
    AlertTriangle,
    TrendingUp,
    Lock,
    MessageSquare,
    FileText
} from 'lucide-react';
import { formatSmartDate } from '@/lib/utils/date';
import { cn } from '@/lib/utils/cn';
import toast from 'react-hot-toast';

interface TicketDetailSheetProps {
    ticketId: string | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function TicketDetailSheet({ ticketId, open, onOpenChange }: TicketDetailSheetProps) {
    const [comment, setComment] = useState('');
    const [isInternal, setIsInternal] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const queryClient = useQueryClient();

    const { data: ticket, isLoading } = useQuery({
        queryKey: ['ticket', ticketId],
        queryFn: async () => {
            if (!ticketId) return null;
            const [data, error] = await ticketsAPI.getById(ticketId);
            if (error) throw new Error(error.message);
            return data;
        },
        enabled: !!ticketId && open,
    });

    const commentMutation = useMutation({
        mutationFn: async () => {
            if (!ticketId || !comment.trim()) return;
            const [data, error] = await ticketsAPI.addComment(ticketId, comment, isInternal);
            if (error) throw new Error(error.message);
            return data;
        },
        onSuccess: () => {
            setComment('');
            queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] });
            // Scroll to bottom?
        },
        onError: (error: Error) => toast.error(`Failed to post comment: ${error.message}`),
    });

    const getPriorityInfo = (priority: string) => {
        switch (priority) {
            case 'urgent': return { color: 'text-red-600 bg-red-50 border-red-200', icon: AlertTriangle, label: 'Urgent', badgeColor: 'bg-red-500/20 text-red-100 border-red-400/30' };
            case 'high': return { color: 'text-orange-600 bg-orange-50 border-orange-200', icon: TrendingUp, label: 'High', badgeColor: 'bg-orange-500/20 text-orange-100 border-orange-400/30' };
            case 'medium': return { color: 'text-yellow-600 bg-yellow-50 border-yellow-200', icon: AlertCircle, label: 'Medium', badgeColor: 'bg-yellow-500/20 text-yellow-100 border-yellow-400/30' };
            default: return { color: 'text-gray-600 bg-gray-50 border-gray-200', icon: CheckCircle2, label: 'Low', badgeColor: 'bg-blue-500/20 text-blue-100 border-blue-400/30' };
        }
    };

    if (!ticketId) return null;

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent className="sm:max-w-xl w-full p-0 overflow-hidden bg-white dark:bg-zinc-950 border-l border-border shadow-2xl">
                <div className="sr-only">
                    <SheetTitle>Ticket Details</SheetTitle>
                </div>

                {isLoading ? (
                    <div className="h-full flex items-center justify-center">
                        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : ticket ? (
                    <div className="flex flex-col h-full">
                        {/* Header with Gradient */}
                        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-8 text-white shrink-0 relative overflow-hidden">
                            {/* Decorative background element */}
                            <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none" />

                            <div className="relative z-10">
                                <div className="flex items-center gap-2 mb-4">
                                    <Badge variant="secondary" className="bg-white/20 text-white hover:bg-white/30 border-0 backdrop-blur-md px-3 capitalize">
                                        {ticket.status.replace('_', ' ')}
                                    </Badge>
                                    {(() => {
                                        const pInfo = getPriorityInfo(ticket.priority);
                                        const PIcon = pInfo.icon;
                                        return (
                                            <Badge className={cn("border backdrop-blur-md px-3 flex items-center gap-1.5", pInfo.badgeColor)}>
                                                <PIcon className="w-3.5 h-3.5" />
                                                <span>{ticket.priority} Priority</span>
                                            </Badge>
                                        );
                                    })()}
                                </div>
                                {/* Ticket Title (Visible) */}
                                <div className="text-2xl font-bold text-white mb-3 tracking-tight leading-snug">
                                    {ticket.title}
                                </div>

                                <div className="flex items-center gap-6 mt-6 text-sm font-medium text-blue-100">
                                    <div className="flex items-center gap-2 bg-blue-500/20 px-3 py-1.5 rounded-full border border-blue-400/30">
                                        <Clock className="w-4 h-4" />
                                        <span>{formatSmartDate(ticket.created_at)}</span>
                                    </div>
                                    <div className="flex items-center gap-2 bg-blue-500/20 px-3 py-1.5 rounded-full border border-blue-400/30">
                                        <User className="w-4 h-4" />
                                        <span>{ticket.patient_id.slice(0, 8)}...</span>
                                    </div>
                                    <div className="flex items-center gap-2 bg-blue-500/20 px-3 py-1.5 rounded-full border border-blue-400/30 capitalize">
                                        <div className="w-2 h-2 rounded-full bg-white" />
                                        <span>{ticket.category}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Scrollable Content */}
                        <ScrollArea className="flex-1">
                            <div className="p-8 pb-12">
                                {/* Description Card */}
                                <div className="bg-card rounded-xl p-5 border border-border shadow-sm mb-8">
                                    <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                                        <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-md">
                                            <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                                        </div>
                                        Description
                                    </h3>
                                    <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                                        {ticket.description}
                                    </p>
                                </div>

                                {/* Comments Timeline */}
                                <div className="space-y-8">
                                    <h3 className="text-lg font-bold flex items-center gap-2 text-foreground">
                                        <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                            <MessageSquare className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                                        </div>
                                        Timeline
                                    </h3>

                                    <div className="relative pl-2">
                                        {/* Vertical Guide Line */}
                                        <div className="absolute left-[15px] top-4 bottom-0 w-0.5 bg-border top-8" />

                                        {ticket.comments?.map((comment) => (
                                            <div key={comment.id} className="relative pl-10 mb-8 last:mb-0 group">
                                                {/* Avatar/Dot */}
                                                <div className={cn(
                                                    "absolute left-0 top-0 w-8 h-8 rounded-full border-4 border-white dark:border-zinc-950 flex items-center justify-center shadow-sm z-10",
                                                    comment.is_internal ? "bg-amber-100" : "bg-blue-100"
                                                )}>
                                                    {comment.is_internal ? (
                                                        <Lock className="w-3.5 h-3.5 text-amber-600" />
                                                    ) : (
                                                        <User className="w-3.5 h-3.5 text-blue-600" />
                                                    )}
                                                </div>

                                                <div className="bg-card rounded-xl p-4 border border-border shadow-sm hover:shadow-md hover:border-blue-200 dark:hover:border-blue-800 transition-all duration-200">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-sm font-semibold text-foreground">
                                                                User
                                                            </span>
                                                            <span className="text-xs text-muted-foreground">
                                                                {formatSmartDate(comment.created_at)}
                                                            </span>
                                                        </div>
                                                        {comment.is_internal && (
                                                            <Badge variant="secondary" className="h-5 text-[10px] bg-amber-50 text-amber-700 hover:bg-amber-100 border-amber-100 px-1.5 gap-1">
                                                                Internal Note
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    <p className={cn(
                                                        "text-sm leading-relaxed",
                                                        comment.is_internal ? "text-amber-900" : "text-foreground"
                                                    )}>
                                                        {comment.comment}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}

                                        {(!ticket.comments || ticket.comments.length === 0) && (
                                            <div className="pl-10 text-sm text-muted-foreground italic py-2">
                                                No comments yet. Be the first to reply.
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </ScrollArea>

                        {/* Footer Input */}
                        <div className="p-6 border-t border-border bg-gray-50/50 dark:bg-zinc-900/50 shrink-0">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-sm font-medium text-foreground">Add Response</span>
                                <div className="flex items-center gap-2">
                                    <Switch
                                        id="internal-mode"
                                        checked={isInternal}
                                        onCheckedChange={setIsInternal}
                                    />
                                    <Label htmlFor="internal-mode" className="text-xs text-muted-foreground flex items-center gap-1 cursor-pointer select-none">
                                        {isInternal ? <Lock className="w-3 h-3 text-amber-600" /> : null}
                                        Internal Note
                                    </Label>
                                </div>
                            </div>

                            <div className="relative">
                                <Textarea
                                    value={comment}
                                    onChange={(e) => setComment(e.target.value)}
                                    placeholder={isInternal ? "Add an internal note (visible only to team)..." : "Type your reply..."}
                                    className={cn(
                                        "min-h-[100px] resize-none pr-12 bg-white dark:bg-zinc-950 shadow-sm",
                                        isInternal && "bg-amber-50/30 border-amber-200/50 focus-visible:ring-amber-500/20"
                                    )}
                                />
                                <Button
                                    size="icon"
                                    className={cn(
                                        "absolute bottom-3 right-3 h-8 w-8 transition-colors shadow-sm",
                                        isInternal ? "bg-amber-600 hover:bg-amber-700" : "bg-blue-600 hover:bg-blue-700"
                                    )}
                                    disabled={!comment.trim() || commentMutation.isPending}
                                    onClick={() => commentMutation.mutate()}
                                >
                                    <Send className="w-4 h-4 text-white" />
                                </Button>
                            </div>
                        </div>
                    </div>
                ) : null}
            </SheetContent>
        </Sheet>
    );
}
