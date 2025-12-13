"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Activity, FileText, Layout, Zap, Calendar, Heart, Stethoscope, Briefcase } from 'lucide-react';
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
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { journeysAPI } from "@/lib/api/journeys";
import toast from "react-hot-toast";
import { cn } from "@/lib/utils/cn";

const formSchema = z.object({
    name: z.string().min(2, {
        message: "Name must be at least 2 characters.",
    }),
    description: z.string().optional(),
    journey_type: z.enum(["opd", "ipd", "procedure", "chronic_care", "wellness"]),
    is_default: z.boolean().default(false),
});

interface CreateJourneyDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function CreateJourneyDialog({
    open,
    onOpenChange,
    onSuccess,
}: CreateJourneyDialogProps) {
    const [loading, setLoading] = useState(false);

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
            journey_type: "wellness",
            is_default: false,
        },
    });

    async function onSubmit(values: z.infer<typeof formSchema>) {
        setLoading(true);
        try {
            const [data, error] = await journeysAPI.create({
                tenant_id: "00000000-0000-0000-0000-000000000001", // Hardcoded for demo
                ...values,
            });

            if (error) {
                toast.error(error.message || "Failed to create journey");
                return;
            }

            toast.success("Journey created successfully");
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

    const getTypeIcon = (type: string) => {
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
            <DialogContent className="sm:max-w-[600px] p-0 overflow-hidden border-0 shadow-2xl">
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
                    <DialogHeader>
                        <DialogTitle className="text-xl font-bold flex items-center gap-2">
                            <Layout className="w-5 h-5 text-blue-100" />
                            Create New Journey
                        </DialogTitle>
                        <DialogDescription className="text-blue-100/90 text-sm">
                            Design a new care pathway to automate patient tracking and engagement.
                        </DialogDescription>
                    </DialogHeader>
                </div>

                <div className="p-6 bg-white dark:bg-zinc-950">
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Name Input */}
                                <FormField
                                    control={form.control}
                                    name="name"
                                    render={({ field }) => (
                                        <FormItem className="col-span-2">
                                            <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                                <FileText className="w-4 h-4 text-blue-600" />
                                                Journey Name
                                            </FormLabel>
                                            <FormControl>
                                                <Input
                                                    placeholder="e.g. Post-Surgery Recovery Program"
                                                    {...field}
                                                    className="h-10 border-gray-200 focus:border-blue-500 focus:ring-blue-100 bg-gray-50/50"
                                                />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                {/* Type Selection */}
                                <FormField
                                    control={form.control}
                                    name="journey_type"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                                {getTypeIcon(field.value)}
                                                Journey Type
                                            </FormLabel>
                                            <Select
                                                onValueChange={field.onChange}
                                                defaultValue={field.value}
                                            >
                                                <FormControl>
                                                    <SelectTrigger className="h-10 border-gray-200 bg-gray-50/50 focus:ring-blue-100">
                                                        <SelectValue placeholder="Select type" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    <SelectItem value="opd">Outpatient (OPD)</SelectItem>
                                                    <SelectItem value="ipd">Inpatient (IPD)</SelectItem>
                                                    <SelectItem value="procedure">Procedure</SelectItem>
                                                    <SelectItem value="chronic_care">Chronic Care</SelectItem>
                                                    <SelectItem value="wellness">Wellness</SelectItem>
                                                </SelectContent>
                                            </Select>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                {/* Default Switch */}
                                <FormField
                                    control={form.control}
                                    name="is_default"
                                    render={({ field }) => (
                                        <FormItem className="flex flex-row items-center justify-between rounded-xl border border-gray-200 p-3 shadow-sm bg-gray-50/50 hover:bg-white hover:border-blue-200 transition-all cursor-pointer">
                                            <div className="space-y-0.5">
                                                <FormLabel className="text-sm font-semibold text-gray-700 cursor-pointer">
                                                    Auto-Apply
                                                </FormLabel>
                                                <FormDescription className="text-xs text-gray-500">
                                                    Make default for type
                                                </FormDescription>
                                            </div>
                                            <FormControl>
                                                <Switch
                                                    checked={field.value}
                                                    onCheckedChange={field.onChange}
                                                    className="data-[state=checked]:bg-blue-600"
                                                />
                                            </FormControl>
                                        </FormItem>
                                    )}
                                />

                                {/* Description */}
                                <FormField
                                    control={form.control}
                                    name="description"
                                    render={({ field }) => (
                                        <FormItem className="col-span-2">
                                            <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                                <Briefcase className="w-4 h-4 text-gray-500" />
                                                Description
                                            </FormLabel>
                                            <FormControl>
                                                <Textarea
                                                    placeholder="Describe the clinical goals and protocols for this journey..."
                                                    {...field}
                                                    className="resize-none min-h-[100px] border-gray-200 focus:border-blue-500 focus:ring-blue-100 bg-gray-50/50"
                                                />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>

                            <DialogFooter className="pt-4 border-t border-gray-100">
                                <Button
                                    variant="outline"
                                    type="button"
                                    onClick={() => onOpenChange(false)}
                                    className="border-gray-200 hover:bg-gray-100 hover:text-gray-900"
                                >
                                    Cancel
                                </Button>
                                <Button
                                    type="submit"
                                    disabled={loading}
                                    className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20"
                                >
                                    {loading ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                            Creating...
                                        </>
                                    ) : (
                                        "Create Journey"
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
