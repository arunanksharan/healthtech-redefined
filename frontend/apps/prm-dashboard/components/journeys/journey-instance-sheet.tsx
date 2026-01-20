"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
    Route,
    Calendar,
    CheckCircle2,
    Clock,
    ArrowRight,
    Play,
    PauseCircle,
    StopCircle,
} from 'lucide-react';
import { journeysAPI } from '@/lib/api/journeys';
import { formatSmartDate } from '@/lib/utils/date';
import toast from "react-hot-toast";
import { cn } from "@/lib/utils/cn";

interface JourneyInstanceSheetProps {
    instanceId: string | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function JourneyInstanceSheet({ instanceId, open, onOpenChange }: JourneyInstanceSheetProps) {
    const queryClient = useQueryClient();
    const [advanceNotes, setAdvanceNotes] = useState("");
    const [isAdvancing, setIsAdvancing] = useState(false);

    // Fetch instance details
    const { data: instance, isLoading } = useQuery({
        queryKey: ['journey-instance', instanceId],
        queryFn: async () => {
            if (!instanceId) return null;
            const [data, error] = await journeysAPI.getInstance(instanceId);
            if (error) throw new Error(error.message);
            return data;
        },
        enabled: !!instanceId && open,
    });

    // Advance Stage Mutation
    const advanceMutation = useMutation({
        mutationFn: async () => {
            if (!instanceId) return;
            const [data, error] = await journeysAPI.advanceStage(instanceId, advanceNotes);
            if (error) throw new Error(error.message);
            return data;
        },
        onSuccess: () => {
            toast.success("Journey advanced to next stage");
            setAdvanceNotes("");
            setIsAdvancing(false);
            queryClient.invalidateQueries({ queryKey: ['journey-instance', instanceId] });
            queryClient.invalidateQueries({ queryKey: ['patient-360'] }); // To update list in patient detail
        },
        onError: (error: any) => {
            toast.error(error.message || "Failed to advance stage");
        },
    });

    const currentStageIndex = instance?.stages?.findIndex(s => s.stage_id === instance.current_stage_id) ?? -1;
    const nextStage = instance?.stages && currentStageIndex !== -1 && currentStageIndex < instance.stages.length - 1
        ? instance.stages[currentStageIndex + 1]
        : null;

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'bg-green-100 text-green-700';
            case 'completed': return 'bg-blue-100 text-blue-700';
            case 'paused': return 'bg-amber-100 text-amber-700';
            case 'cancelled': return 'bg-red-100 text-red-700';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent className="sm:max-w-xl w-full p-0 overflow-hidden bg-white dark:bg-zinc-950 border-l border-border shadow-2xl">
                <SheetHeader className="sr-only">
                    <SheetTitle>Journey Instance Details</SheetTitle>
                    <SheetDescription>Details of the selected patient journey instance</SheetDescription>
                </SheetHeader>
                {isLoading ? (
                    <div className="h-full flex items-center justify-center">
                        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : instance ? (
                    <div className="flex flex-col h-full">
                        {/* Header */}
                        <div className="bg-gradient-to-r from-teal-600 to-emerald-600 p-8 text-white shrink-0 relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none" />
                            <div className="relative z-10">
                                <div className="flex items-center gap-2 mb-4">
                                    <Badge className={cn("border-0 backdrop-blur-md px-3", getStatusColor(instance.status).replace('bg-', 'bg-white/20 text-white '))}>
                                        {instance.status}
                                    </Badge>
                                    <Badge variant="outline" className="text-emerald-100 border-emerald-400/30">
                                        Instance #{instance.id.slice(0, 8)}
                                    </Badge>
                                </div>
                                <h2 className="text-2xl font-bold text-white mb-2">
                                    {instance.journey_name || "Care Journey"}
                                </h2>
                                <div className="flex items-center gap-4 text-sm text-emerald-100">
                                    <span>Started {formatSmartDate(instance.start_date)}</span>
                                </div>
                            </div>
                        </div>

                        {/* Content */}
                        <ScrollArea className="flex-1">
                            <div className="p-8 pb-12 space-y-8">
                                {/* Current Progress */}
                                {instance.status === 'active' && nextStage && (
                                    <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-5">
                                        <h3 className="text-emerald-900 font-semibold mb-1 flex items-center gap-2">
                                            <Play className="w-4 h-4 fill-emerald-600 text-emerald-600" />
                                            Active Stage
                                        </h3>
                                        <p className="text-emerald-700 mb-4 text-sm">
                                            Currently in <strong>{instance.current_stage_name}</strong>.
                                            Target completion: {formatSmartDate(new Date(Date.now() + 86400000))} (estimated)
                                        </p>

                                        {!isAdvancing ? (
                                            <Button
                                                onClick={() => setIsAdvancing(true)}
                                                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                                            >
                                                Advance to {nextStage.name}
                                                <ArrowRight className="w-4 h-4 ml-2" />
                                            </Button>
                                        ) : (
                                            <div className="space-y-3 bg-white p-3 rounded-lg border border-emerald-100">
                                                <Textarea
                                                    placeholder="Add completion notes (optional)..."
                                                    value={advanceNotes}
                                                    onChange={(e) => setAdvanceNotes(e.target.value)}
                                                    className="min-h-[80px] text-sm"
                                                />
                                                <div className="flex gap-2">
                                                    <Button
                                                        size="sm"
                                                        variant="ghost"
                                                        onClick={() => setIsAdvancing(false)}
                                                        className="flex-1"
                                                    >
                                                        Cancel
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        onClick={() => advanceMutation.mutate()}
                                                        disabled={advanceMutation.isPending}
                                                        className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                                                    >
                                                        {advanceMutation.isPending ? "Advancing..." : "Confirm Advance"}
                                                    </Button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Timeline */}
                                <div className="space-y-8">
                                    <h3 className="font-semibold text-foreground flex items-center gap-2">
                                        <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                            <Route className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                                        </div>
                                        Journey Timeline
                                    </h3>

                                    <div className="relative pl-1">
                                        {instance.stages?.map((stage, index) => {
                                            const isCompleted = index < currentStageIndex || instance.status === 'completed';
                                            const isCurrent = index === currentStageIndex && instance.status !== 'completed';

                                            // Colors based on status
                                            const dotColorClass = isCompleted
                                                ? "bg-blue-600 text-white border-blue-600"
                                                : isCurrent
                                                    ? "bg-emerald-600 text-white shadow-lg shadow-emerald-200 border-white"
                                                    : "bg-white text-gray-500 border-gray-200";

                                            const lineColorClass = index !== (instance.stages?.length || 0) - 1
                                                ? (isCompleted ? "bg-blue-200" : "bg-gray-100")
                                                : "";

                                            const cardClass = isCurrent
                                                ? "bg-white border-emerald-200 shadow-md ring-1 ring-emerald-100"
                                                : "bg-card border-border shadow-sm";

                                            const triangleClass = isCurrent
                                                ? "bg-white border-l border-t border-emerald-200"
                                                : "bg-card border-l border-t border-border";

                                            return (
                                                <div key={stage.stage_id} className="flex gap-4 group mb-0">
                                                    {/* Left Column: Timeline Line & Indicator */}
                                                    <div className="flex flex-col items-center min-h-[100px]">
                                                        {/* Number Badge/Icon */}
                                                        <div className={cn(
                                                            "relative z-10 flex items-center justify-center w-8 h-8 rounded-full border-4 shrink-0 transition-all duration-200",
                                                            dotColorClass,
                                                            isCurrent && "scale-110"
                                                        )}>
                                                            {isCompleted ? <CheckCircle2 className="w-4 h-4" /> :
                                                                isCurrent ? <Play className="w-3 h-3 fill-current" /> :
                                                                    <span className="text-xs font-bold">{index + 1}</span>}
                                                        </div>

                                                        {/* Connecting Line */}
                                                        {index !== (instance.stages?.length || 0) - 1 && (
                                                            <div className={cn("flex-1 w-0.5 my-1 transition-colors", lineColorClass)} />
                                                        )}
                                                    </div>

                                                    {/* Right Column: Content Card */}
                                                    <div className="flex-1 pb-8">
                                                        <div className={cn("rounded-xl p-5 border transition-all duration-200 relative top-[-6px]", cardClass)}>
                                                            {/* Triangle pointing to timeline */}
                                                            <div className={cn("absolute top-4 -left-2 w-4 h-4 transform -rotate-45 transition-colors", triangleClass)} />

                                                            <div className="flex items-center justify-between mb-2">
                                                                <h4 className={cn("font-semibold text-base", isCurrent ? "text-emerald-900" : "text-foreground")}>
                                                                    {stage.name}
                                                                </h4>
                                                                {isCompleted && (
                                                                    <Badge variant="secondary" className="bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-100">
                                                                        Completed
                                                                    </Badge>
                                                                )}
                                                                {isCurrent && (
                                                                    <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-200 border-emerald-200">
                                                                        Active
                                                                    </Badge>
                                                                )}
                                                            </div>

                                                            <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">
                                                                {stage.description}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        </ScrollArea>
                    </div>
                ) : (
                    <div className="h-full flex items-center justify-center text-muted-foreground">
                        Instance not found
                    </div>
                )}
            </SheetContent>
        </Sheet>
    );
}
