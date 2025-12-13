"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useQuery } from "@tanstack/react-query";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { journeysAPI } from "@/lib/api/journeys";
import { Route, Play, Stethoscope, Activity, Zap, Heart, Calendar, Briefcase, X } from "lucide-react";
import toast from "react-hot-toast";

const formSchema = z.object({
    journey_id: z.string().min(1, { message: "Please select a journey template." }),
});

interface AssignJourneyDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    patientId: string;
    onSuccess: () => void;
}

export function AssignJourneyDialog({
    open,
    onOpenChange,
    patientId,
    onSuccess,
}: AssignJourneyDialogProps) {
    const [loading, setLoading] = useState(false);

    // Fetch active journey templates
    const { data: journeysData } = useQuery({
        queryKey: ["journey-templates"],
        queryFn: async () => {
            const [data, err] = await journeysAPI.getAll({ status: "active", limit: 100 });
            if (err) throw new Error(err.message);
            return data;
        },
        enabled: open,
    });

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            journey_id: "",
        },
    });

    async function onSubmit(values: z.infer<typeof formSchema>) {
        setLoading(true);
        try {
            const [data, error] = await journeysAPI.createInstance({
                tenant_id: "00000000-0000-0000-0000-000000000001", // Demo tenant
                patient_id: patientId,
                journey_id: values.journey_id,
            });

            if (error) {
                toast.error(error.message || "Failed to start journey");
                return;
            }

            toast.success("Journey started successfully");
            form.reset();
            onSuccess();
            onOpenChange(false);
        } catch (error) {
            toast.error("An unexpected error occurred");
            console.error(error);
        } finally {
            setLoading(false);
        }
    }

    const getTypeIcon = (type?: string) => {
        switch (type) {
            case 'opd': return <Stethoscope className="w-4 h-4 text-blue-500" />;
            case 'ipd': return <Activity className="w-4 h-4 text-purple-500" />;
            case 'procedure': return <Zap className="w-4 h-4 text-amber-500" />;
            case 'chronic_care': return <Heart className="w-4 h-4 text-red-500" />;
            case 'wellness': return <Calendar className="w-4 h-4 text-green-500" />;
            default: return <Briefcase className="w-4 h-4 text-gray-500" />;
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[480px] p-0 overflow-hidden border-0 shadow-2xl [&>button]:hidden">
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-8 text-white relative overflow-hidden">
                    {/* Close Button */}
                    <button
                        type="button"
                        onClick={() => onOpenChange(false)}
                        className="absolute right-4 top-4 p-2 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors z-50 focus:outline-none focus:ring-2 focus:ring-white/50"
                    >
                        <X className="w-4 h-4" />
                    </button>

                    {/* Decorative background element */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none" />

                    <DialogHeader className="relative z-10">
                        <DialogTitle className="text-2xl font-bold flex items-center gap-3 text-white">
                            <div className="p-2 bg-white/10 rounded-lg backdrop-blur-sm">
                                <Play className="w-5 h-5 text-white" />
                            </div>
                            Start Care Journey
                        </DialogTitle>
                        <DialogDescription className="text-blue-50/90 text-sm mt-2 max-w-sm leading-relaxed">
                            Assign a new care pathway to this patient. The journey will start immediately.
                        </DialogDescription>
                    </DialogHeader>
                </div>

                <div className="p-8 bg-white dark:bg-zinc-950">
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                            <FormField
                                control={form.control}
                                name="journey_id"
                                render={({ field }) => (
                                    <FormItem className="space-y-4">
                                        <FormLabel className="text-gray-900 font-semibold flex items-center gap-2 text-base">
                                            <Route className="w-5 h-5 text-blue-600" />
                                            Select Journey Template
                                        </FormLabel>
                                        <Select
                                            onValueChange={field.onChange}
                                            defaultValue={field.value}
                                        >
                                            <FormControl>
                                                <SelectTrigger className="h-14 border-gray-200 bg-gray-50 hover:bg-white hover:border-blue-200 focus:ring-blue-100 transition-all text-base rounded-xl">
                                                    <SelectValue placeholder="Choose a journey pathway..." />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent className="max-h-[300px]">
                                                {journeysData?.journeys?.map((journey) => (
                                                    <SelectItem key={journey.id} value={journey.id} className="py-3">
                                                        <div className="flex items-center gap-3">
                                                            <div className="p-2 bg-gray-50 rounded-md">
                                                                {getTypeIcon(journey.journey_type)}
                                                            </div>
                                                            <div className="flex flex-col">
                                                                <span className="font-medium text-gray-900">{journey.name}</span>
                                                                {journey.description && (
                                                                    <span className="text-xs text-gray-500 line-clamp-1">{journey.description}</span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </SelectItem>
                                                ))}
                                                {(!journeysData?.journeys || journeysData.journeys.length === 0) && (
                                                    <div className="px-4 py-8 text-sm text-gray-500 text-center flex flex-col items-center gap-2">
                                                        <Briefcase className="w-8 h-8 text-gray-300" />
                                                        <p>No active templates found</p>
                                                    </div>
                                                )}
                                            </SelectContent>
                                        </Select>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <DialogFooter className="pt-2">
                                <Button
                                    variant="ghost"
                                    type="button"
                                    onClick={() => onOpenChange(false)}
                                    className="text-gray-500 hover:text-gray-900"
                                >
                                    Cancel
                                </Button>
                                <Button
                                    type="submit"
                                    disabled={loading}
                                    className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-600/20 px-8 rounded-xl h-11"
                                >
                                    {loading ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                            Initializing...
                                        </>
                                    ) : (
                                        <>
                                            Start Journey
                                            <Play className="w-4 h-4 ml-2 fill-current" />
                                        </>
                                    )}
                                </Button>
                            </DialogFooter>
                        </form>
                    </Form>
                </div>
            </DialogContent>
        </Dialog>
    );
}
