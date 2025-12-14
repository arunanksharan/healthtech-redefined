import { useState } from "react";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from '@/components/ui/sheet';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { journeysAPI } from '@/lib/api/journeys';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import toast from "react-hot-toast";
import {
    Route,
    Calendar,
    CheckCircle2,
    Clock,
    FileText,
    ChevronRight,
    Layout,
    Plus
} from 'lucide-react';
import { formatSmartDate } from '@/lib/utils/date';
import { Separator } from '@/components/ui/separator';

interface JourneyDetailsSheetProps {
    journeyId: string | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function JourneyDetailsSheet({ journeyId, open, onOpenChange }: JourneyDetailsSheetProps) {
    const queryClient = useQueryClient();
    const [isAddingStage, setIsAddingStage] = useState(false);
    const [newStage, setNewStage] = useState({ title: "", description: "" });
    const { data: journey, isLoading } = useQuery({
        queryKey: ['journey', journeyId],
        queryFn: async () => {
            if (!journeyId) return null;
            const [data, error] = await journeysAPI.getById(journeyId);
            if (error) throw new Error(error.message);
            return data;
        },
        enabled: !!journeyId && open,
    });

    const addStageMutation = useMutation({
        mutationFn: async () => {
            if (!journeyId) return;
            const [data, error] = await journeysAPI.addStep(journeyId, {
                title: newStage.title,
                description: newStage.description,
                step_type: 'task'
            });
            if (error) throw new Error(error.message);
            return data;
        },
        onSuccess: () => {
            toast.success("Stage added successfully");
            setNewStage({ title: "", description: "" });
            setIsAddingStage(false);
            queryClient.invalidateQueries({ queryKey: ['journey', journeyId] });
            queryClient.invalidateQueries({ queryKey: ['journey-definitions'] });
        },
        onError: (error: any) => {
            toast.error("Failed to add stage: " + error.message);
        }
    });

    const getJourneyTypeColor = (type?: string) => {
        // Return a clean glassmorphic style for the header
        return 'bg-background/90 backdrop-blur-sm border-0 font-medium px-3';
    };

    const getJourneyTypeText = (type?: string) => {
        switch (type) {
            case 'post_surgery': return 'text-purple-700 dark:text-purple-300';
            case 'chronic_disease': return 'text-rose-700 dark:text-rose-300';
            case 'wellness': return 'text-emerald-700 dark:text-emerald-300';
            case 'pregnancy': return 'text-pink-700 dark:text-pink-300';
            default: return 'text-muted-foreground';
        }
    };

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent className="sm:max-w-xl w-full p-0 overflow-hidden bg-background border-l border-border shadow-2xl">
                <SheetHeader className="sr-only">
                    <SheetTitle>Journey Details</SheetTitle>
                    <SheetDescription>Details and stages of the selected journey template</SheetDescription>
                </SheetHeader>
                {isLoading ? (
                    <div className="h-full flex items-center justify-center">
                        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : journey ? (
                    <div className="flex flex-col h-full">
                        {/* Header with Gradient */}
                        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-8 text-white shrink-0 relative overflow-hidden">
                            {/* Decorative background element */}
                            <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none" />

                            <div className="relative z-10">
                                <div className="flex items-center gap-2 mb-4">
                                    <Badge variant="secondary" className="bg-white/20 text-white hover:bg-white/30 border-0 backdrop-blur-md px-3">
                                        {journey.is_default ? 'Default Template' : 'Custom Template'}
                                    </Badge>
                                    <Badge className={`${getJourneyTypeColor(journey.journey_type)} ${getJourneyTypeText(journey.journey_type)}`}>
                                        {journey.journey_type?.replace('_', ' ')}
                                    </Badge>
                                </div>
                                <h2 className="text-3xl font-bold text-white mb-3 tracking-tight">
                                    {journey.name}
                                </h2>
                                <p className="text-blue-50/90 text-sm leading-relaxed max-w-md">
                                    {journey.description}
                                </p>

                                <div className="flex items-center gap-6 mt-6 text-sm font-medium text-blue-100">
                                    <div className="flex items-center gap-2 bg-blue-500/20 px-3 py-1.5 rounded-full border border-blue-400/30">
                                        <Clock className="w-4 h-4" />
                                        <span>Created {formatSmartDate(journey.created_at)}</span>
                                    </div>
                                    <div className="flex items-center gap-2 bg-blue-500/20 px-3 py-1.5 rounded-full border border-blue-400/30">
                                        <Layout className="w-4 h-4" />
                                        <span>{journey.stages?.length || 0} Stages</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Scrollable Content */}
                        <ScrollArea className="flex-1">
                            <div className="p-8 pb-12">
                                {/* Stages Timeline */}
                                <div className="space-y-8">
                                    <h3 className="text-lg font-bold flex items-center gap-2 text-foreground">
                                        <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                            <Route className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                                        </div>
                                        Journey Stages
                                    </h3>

                                    <div className="relative">
                                        {journey.stages?.map((stage, index) => (
                                            <div key={stage.id} className="flex gap-4 group">
                                                {/* Left Column: Timeline Line & Indicator */}
                                                <div className="flex flex-col items-center min-h-[120px]">
                                                    {/* Number Badge */}
                                                    <div className="relative z-10 flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white shadow-md group-hover:scale-110 transition-transform duration-200 font-bold text-sm border-4 border-white dark:border-zinc-950">
                                                        {index + 1}
                                                    </div>

                                                    {/* Connecting Line */}
                                                    {index !== (journey.stages?.length || 0) - 1 && (
                                                        <div className="flex-1 w-0.5 bg-blue-100 dark:bg-blue-900/30 my-1 group-hover:bg-blue-200 transition-colors" />
                                                    )}
                                                </div>

                                                {/* Right Column: Content Card */}
                                                <div className="flex-1 pb-8">
                                                    <div className="bg-card rounded-xl p-5 border border-border shadow-sm hover:shadow-md hover:border-blue-200 dark:hover:border-blue-800 transition-all duration-200 relative top-[-6px]">
                                                        {/* Triangle pointing to timeline */}
                                                        <div className="absolute top-4 -left-2 w-4 h-4 bg-card border-l border-t border-border transform -rotate-45 group-hover:border-blue-200 dark:group-hover:border-blue-800 transition-colors" />

                                                        <div className="flex items-center justify-between mb-3">
                                                            <h4 className="font-semibold text-foreground text-base">
                                                                {stage.name}
                                                            </h4>
                                                            <Badge variant="secondary" className="bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-100 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800">
                                                                Stage {index + 1}
                                                            </Badge>
                                                        </div>

                                                        <p className="text-sm text-muted-foreground leading-relaxed">
                                                            {stage.description || "No description provided."}
                                                        </p>

                                                        {/* Optional: Add placeholder for tasks if we want to show detail */}
                                                        <div className="mt-4 pt-4 border-t border-border/50 flex gap-4">
                                                            <div className="flex items-center text-xs text-muted-foreground">
                                                                <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-green-500" />
                                                                <span>Tasks configured</span>
                                                            </div>
                                                            <div className="flex items-center text-xs text-muted-foreground">
                                                                <Clock className="w-3.5 h-3.5 mr-1.5 text-blue-500" />
                                                                <span>Duration set</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}

                                        {(!journey.stages || journey.stages.length === 0) && (
                                            <div className="text-center text-muted-foreground text-sm italic py-4">
                                                No stages defined for this journey yet.
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </ScrollArea>

                        {/* Footer (Actions) */}
                        <div className="p-6 border-t border-border bg-muted/30 shrink-0">
                            {!isAddingStage ? (
                                <Button
                                    className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                                    onClick={() => setIsAddingStage(true)}
                                >
                                    <Plus className="w-4 h-4 mr-2" />
                                    Add New Stage
                                </Button>
                            ) : (
                                <div className="space-y-4 bg-card p-4 rounded-xl border border-border shadow-sm">
                                    <h4 className="font-semibold text-sm">New Stage Details</h4>
                                    <Input
                                        placeholder="Stage Title (e.g. Initial Consultation)"
                                        value={newStage.title}
                                        onChange={(e) => setNewStage({ ...newStage, title: e.target.value })}
                                    />
                                    <Textarea
                                        placeholder="Description of this stage..."
                                        value={newStage.description}
                                        onChange={(e) => setNewStage({ ...newStage, description: e.target.value })}
                                        className="min-h-[80px]"
                                    />
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="flex-1"
                                            onClick={() => setIsAddingStage(false)}
                                        >
                                            Cancel
                                        </Button>
                                        <Button
                                            size="sm"
                                            className="flex-1 bg-blue-600 text-white"
                                            onClick={() => addStageMutation.mutate()}
                                            disabled={!newStage.title || addStageMutation.isPending}
                                        >
                                            {addStageMutation.isPending ? "Adding..." : "Save Stage"}
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="h-full flex items-center justify-center text-muted-foreground">
                        Journey not found
                    </div>
                )}
            </SheetContent>
        </Sheet>
    );
}
