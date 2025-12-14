'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    Route,
    Plus,
    Search,
    Filter,
    CheckCircle2,
    Clock,
    Activity,
    User,
    Calendar,
    MoreVertical,
    Pause,
    Play,
    ArrowRight,
    TrendingUp,
} from 'lucide-react';
import { journeysAPI } from '@/lib/api/journeys';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { formatSmartDate } from '@/lib/utils/date';
import { cn } from '@/lib/utils/cn';
import toast from 'react-hot-toast';
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

import { CreateJourneyDialog } from '@/components/journeys/create-journey-dialog';
import { JourneyDetailsSheet } from '@/components/journeys/journey-details-sheet';

export default function JourneysPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
    const [selectedJourneyId, setSelectedJourneyId] = useState<string | null>(null);
    const [isDetailsOpen, setIsDetailsOpen] = useState(false);

    // Fetch all journey definitions
    const { data: journeysData, isLoading, error, refetch } = useQuery({
        queryKey: ['journey-definitions', statusFilter],
        queryFn: async () => {
            const [data, error] = await journeysAPI.getAll();
            if (error) throw new Error(error.message);
            return data;
        },
    });

    const journeys = journeysData?.journeys || [];
    const filteredJourneys = journeys.filter(journey =>
        searchQuery === '' ||
        journey.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        journey.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        journey.journey_type?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const stats = {
        total: journeys.length,
        active: journeys.filter(j => j.is_default).length,
        completed: 0,
        paused: 0,
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800';
            case 'completed': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800';
            case 'paused': return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800';
            case 'cancelled': return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800';
            default: return 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700';
        }
    };

    const getJourneyTypeColor = (type: string) => {
        switch (type) {
            case 'post_surgery': return 'bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800';
            case 'chronic_disease': return 'bg-rose-50 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800';
            case 'wellness': return 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800';
            case 'pregnancy': return 'bg-pink-50 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 border-pink-200 dark:border-pink-800';
            default: return 'bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-800';
        }
    };

    const getProgressPercentage = (journey: any) => {
        if (!journey.steps || journey.steps.length === 0) return 0;
        const completedSteps = journey.steps.filter((s: any) => s.status === 'completed').length;
        return Math.round((completedSteps / journey.steps.length) * 100);
    };

    return (
        <div className="flex flex-col min-h-screen bg-muted/40">
            {/* Sticky Glassmorphic Header */}
            <header className="sticky top-0 z-30 flex items-center justify-between p-6 bg-background/80 backdrop-blur-md border-b border-border/50 supports-[backdrop-filter]:bg-background/60">
                <div>
                    <h1 className="text-2xl font-bold text-foreground tracking-tight">Care Journeys</h1>
                    <p className="text-sm text-muted-foreground mt-1">Manage patient care pathways and recovery plans</p>
                </div>
                <div className="flex gap-3">
                    <Button
                        onClick={() => setIsCreateDialogOpen(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-all hover:scale-105"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        New Journey
                    </Button>
                </div>
            </header>

            <div className="p-6 space-y-6">
                {/* Magic Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--info) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Total Journeys</CardTitle>
                            <Route className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">
                                <NumberTicker value={stats.total} />
                            </div>
                            <div className="flex items-center mt-1 text-xs text-blue-600 dark:text-blue-400">
                                <TrendingUp className="w-3 h-3 mr-1" />
                                <span>Active tracking</span>
                            </div>
                        </CardContent>
                    </MagicCard>

                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--success) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Active</CardTitle>
                            <Activity className="w-4 h-4 text-green-600 dark:text-green-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">
                                <NumberTicker value={stats.active} />
                            </div>
                            <div className="mt-1 text-xs text-muted-foreground">Currently progressing</div>
                        </CardContent>
                    </MagicCard>

                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--info) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Completed</CardTitle>
                            <CheckCircle2 className="w-4 h-4 text-blue-500 dark:text-blue-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">
                                <NumberTicker value={stats.completed} />
                            </div>
                            <div className="mt-1 text-xs text-muted-foreground">Successful outcomes</div>
                        </CardContent>
                    </MagicCard>

                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--warning) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Paused</CardTitle>
                            <Pause className="w-4 h-4 text-amber-500 dark:text-amber-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">
                                <NumberTicker value={stats.paused} />
                            </div>
                            <div className="mt-1 text-xs text-muted-foreground">Requires attention</div>
                        </CardContent>
                    </MagicCard>
                </div>

                {/* Search & Filters */}
                <div className="bg-card p-4 rounded-xl border border-border shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
                    <div className="relative w-full md:w-96">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                            placeholder="Search by patient or journey title..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 bg-muted/50 border-border focus:bg-background transition-all"
                        />
                    </div>
                    <div className="flex items-center gap-3 w-full md:w-auto">
                        <div className="flex items-center bg-muted/50 p-1 rounded-lg border border-border">
                            {['all', 'active', 'completed', 'paused'].map((filter) => (
                                <button
                                    key={filter}
                                    onClick={() => setStatusFilter(filter)}
                                    className={cn(
                                        "px-3 py-1.5 text-xs font-medium rounded-md transition-all capitalize",
                                        statusFilter === filter
                                            ? "bg-background text-foreground shadow-sm"
                                            : "text-muted-foreground hover:text-foreground"
                                    )}
                                >
                                    {filter}
                                </button>
                            ))}
                        </div>
                        <Button variant="outline" size="sm" className="hidden md:flex">
                            <Filter className="w-4 h-4 mr-2" />
                            Filter
                        </Button>
                    </div>
                </div>

                {/* Journeys List */}
                {isLoading ? (
                    <div className="flex justify-center py-12">
                        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : filteredJourneys.length === 0 ? (
                    <div className="text-center py-12 bg-card rounded-xl border border-border border-dashed">
                        <Route className="w-12 h-12 mx-auto mb-3 text-muted" />
                        <h3 className="text-lg font-medium text-foreground">No journeys found</h3>
                        <p className="text-sm text-muted-foreground">Try adjusting your filters or create a new journey</p>
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {filteredJourneys.map((journey) => (
                            <div
                                key={journey.id}
                                className="group bg-card rounded-xl border border-border p-5 hover:border-blue-300 hover:shadow-md transition-all duration-200"
                            >
                                <div className="flex flex-col md:flex-row gap-6">
                                    {/* Journey Icon */}
                                    <div className={cn(
                                        "w-12 h-12 rounded-xl flex items-center justify-center shrink-0",
                                        getJourneyTypeColor(journey.journey_type)
                                    )}>
                                        <Route className="w-6 h-6" />
                                    </div>

                                    {/* Main Content */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <h3 className="text-lg font-semibold text-foreground group-hover:text-blue-600 transition-colors">
                                                    {journey.name}
                                                </h3>
                                                <div className="flex items-center gap-4 mt-1">
                                                    <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                                                        <Route className="w-4 h-4 text-muted-foreground" />
                                                        <span className="font-medium text-foreground/80">{journey.stages?.length || 0} Stages</span>
                                                    </div>
                                                    <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                                                        <Calendar className="w-4 h-4" />
                                                        <span>Created {formatSmartDate(journey.created_at)}</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Status Badge */}
                                            <Badge variant="secondary" className={cn("capitalize px-2.5 py-0.5", journey.is_default ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700')}>
                                                {journey.is_default ? 'Default' : journey.journey_type}
                                            </Badge>
                                        </div>

                                        {/* Description */}
                                        <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
                                            {journey.description}
                                        </p>

                                        {/* Stages Timeline Preview */}
                                        {journey.stages && journey.stages.length > 0 && (
                                            <div className="mt-4 flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
                                                {journey.stages.slice(0, 5).map((stage: any, idx: number) => (
                                                    <div key={idx} className="flex items-center shrink-0">
                                                        <div className="flex items-start gap-2 px-3 py-1.5 rounded-lg border bg-card border-border/50 text-muted-foreground text-xs whitespace-nowrap transition-colors">
                                                            <div className="w-3.5 h-3.5 rounded-full border border-blue-400 flex items-center justify-center text-[10px] font-medium text-blue-600">
                                                                {stage.order_index}
                                                            </div>
                                                            <span>{stage.name}</span>
                                                        </div>
                                                        {idx < Math.min(journey.stages.length, 5) - 1 && (
                                                            <ArrowRight className="w-3 h-3 text-muted mx-1" />
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Actions */}
                                    <div className="flex md:flex-col items-center justify-center gap-2 border-t md:border-t-0 md:border-l border-border/50 pt-4 md:pt-0 md:pl-6">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="w-full whitespace-nowrap"
                                            onClick={() => {
                                                setSelectedJourneyId(journey.id);
                                                setIsDetailsOpen(true);
                                            }}
                                        >
                                            View Details
                                        </Button>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="sm" className="w-full">
                                                    <MoreVertical className="w-4 h-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem>
                                                    <Play className="w-4 h-4 mr-2" /> Resume Journey
                                                </DropdownMenuItem>
                                                <DropdownMenuItem>
                                                    <Pause className="w-4 h-4 mr-2" /> Pause Journey
                                                </DropdownMenuItem>
                                                <DropdownMenuItem className="text-red-600">
                                                    Stop Journey
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <CreateJourneyDialog
                open={isCreateDialogOpen}
                onOpenChange={setIsCreateDialogOpen}
                onSuccess={() => refetch()}
            />

            <JourneyDetailsSheet
                journeyId={selectedJourneyId}
                open={isDetailsOpen}
                onOpenChange={setIsDetailsOpen}
            />
        </div>
    );
}
