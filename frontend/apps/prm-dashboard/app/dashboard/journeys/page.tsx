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
import { Skeleton, CardSkeleton } from '@/components/ui/skeleton';
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

import { CreateJourneyDialog } from '@/components/journeys/create-journey-dialog';
import { JourneyDetailsSheet } from '@/components/journeys/journey-details-sheet';

export default function JourneysPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
    const [selectedJourneyId, setSelectedJourneyId] = useState<string | null>(null);
    const [isDetailsOpen, setIsDetailsOpen] = useState(false);

    // Fetch all journey definitions
    const { data: journeysData, isLoading, isError, error, refetch } = useQuery({
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
            {/* Flat Header */}
            <header className="sticky top-0 z-30 flex items-center justify-between p-6 bg-white dark:bg-gray-900 border-b-2 border-gray-100 dark:border-gray-800">
                <div>
                    <h1 className="text-2xl font-heading text-gray-900 dark:text-white">Care Journeys</h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage patient care pathways and recovery plans</p>
                </div>
                <div className="flex gap-3">
                    <Button
                        onClick={() => setIsCreateDialogOpen(true)}
                        className="flat-btn-primary"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        New Journey
                    </Button>
                </div>
            </header>

            <div className="p-6 space-y-6">
                {/* Flat Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Journeys</span>
                            <Route className="w-5 h-5 text-blue-500" />
                        </div>
                        <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.total}</div>
                        <div className="flex items-center mt-1 text-xs text-blue-600 dark:text-blue-400">
                            <TrendingUp className="w-3 h-3 mr-1" />
                            <span>Active tracking</span>
                        </div>
                    </div>

                    <div className="bg-emerald-50 dark:bg-emerald-900/20 border-2 border-emerald-200 dark:border-emerald-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Active</span>
                            <Activity className="w-5 h-5 text-emerald-500" />
                        </div>
                        <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{stats.active}</div>
                        <div className="mt-1 text-xs text-gray-500">Currently progressing</div>
                    </div>

                    <div className="bg-indigo-50 dark:bg-indigo-900/20 border-2 border-indigo-200 dark:border-indigo-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Completed</span>
                            <CheckCircle2 className="w-5 h-5 text-indigo-500" />
                        </div>
                        <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">{stats.completed}</div>
                        <div className="mt-1 text-xs text-gray-500">Successful outcomes</div>
                    </div>

                    <div className="bg-amber-50 dark:bg-amber-900/20 border-2 border-amber-200 dark:border-amber-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Paused</span>
                            <Pause className="w-5 h-5 text-amber-500" />
                        </div>
                        <div className="text-3xl font-bold text-amber-600 dark:text-amber-400">{stats.paused}</div>
                        <div className="mt-1 text-xs text-gray-500">Requires attention</div>
                    </div>
                </div>

                {/* Flat Search & Filters */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border-2 border-gray-100 dark:border-gray-700 flex flex-col md:flex-row gap-4 items-center justify-between">
                    <div className="relative w-full md:w-96">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <Input
                            placeholder="Search by patient or journey title..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 border-2 border-gray-200 dark:border-gray-600 focus:border-blue-500 bg-gray-50 dark:bg-gray-700 rounded-lg"
                        />
                    </div>
                    <div className="flex items-center gap-3 w-full md:w-auto">
                        <div className="flex items-center bg-gray-100 dark:bg-gray-700 p-1 rounded-lg border-2 border-gray-200 dark:border-gray-600">
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
                    <div className="grid gap-4">
                        {[1, 2, 3, 4].map((i) => <CardSkeleton key={i} />)}
                    </div>
                ) : isError ? (
                    <Alert variant="destructive">
                        <AlertTitle>Error Loading Journeys</AlertTitle>
                        <AlertDescription>{(error as Error)?.message}</AlertDescription>
                    </Alert>
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
