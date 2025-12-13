"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useQuery } from "@tanstack/react-query";
import {
    Ticket,
    User,
    FileText,
    AlertCircle,
    Tag,
    AlignLeft,
} from 'lucide-react';
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
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { ticketsAPI } from "@/lib/api/tickets";
import { patientsAPI } from "@/lib/api/patients";
import toast from "react-hot-toast";

const formSchema = z.object({
    title: z.string().min(5, {
        message: "Title must be at least 5 characters.",
    }),
    patient_id: z.string().min(1, {
        message: "Please select a patient.",
    }),
    category: z.string().min(1, {
        message: "Please select a category.",
    }),
    priority: z.enum(["low", "medium", "high", "urgent"]),
    description: z.string().min(10, {
        message: "Description must be at least 10 characters.",
    }),
});

interface CreateTicketDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function CreateTicketDialog({
    open,
    onOpenChange,
    onSuccess,
}: CreateTicketDialogProps) {
    const [loading, setLoading] = useState(false);

    // Fetch patients for the dropdown
    const { data: patientsData, isLoading: isLoadingPatients } = useQuery({
        queryKey: ["patients-list-simple"],
        queryFn: async () => {
            const [data, err] = await patientsAPI.getAll({ limit: 100 });
            if (err) throw new Error(err.message);
            return data;
        },
        enabled: open, // Only fetch when dialog is open
    });

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            title: "",
            patient_id: "",
            category: "technical",
            priority: "medium",
            description: "",
        },
    });

    async function onSubmit(values: z.infer<typeof formSchema>) {
        setLoading(true);
        try {
            const [data, error] = await ticketsAPI.create({
                tenant_id: "00000000-0000-0000-0000-000000000001", // Hardcoded for demo
                ...values,
            });

            if (error) {
                toast.error(error.message || "Failed to create ticket");
                return;
            }

            toast.success("Ticket created successfully");
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

    const getPriorityIcon = (priority: string) => {
        switch (priority) {
            case 'urgent': return <AlertCircle className="w-4 h-4 text-red-500" />;
            case 'high': return <AlertCircle className="w-4 h-4 text-orange-500" />;
            case 'medium': return <AlertCircle className="w-4 h-4 text-amber-500" />;
            case 'low': return <AlertCircle className="w-4 h-4 text-blue-500" />;
            default: return <AlertCircle className="w-4 h-4 text-gray-500" />;
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] p-0 overflow-hidden border-0 shadow-2xl">
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
                    <DialogHeader>
                        <DialogTitle className="text-xl font-bold flex items-center gap-2">
                            <Ticket className="w-5 h-5 text-blue-100" />
                            Create Support Ticket
                        </DialogTitle>
                        <DialogDescription className="text-blue-100/90 text-sm">
                            Log a new issue or request for a patient.
                        </DialogDescription>
                    </DialogHeader>
                </div>

                <div className="p-6 bg-white dark:bg-zinc-950">
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                            {/* Title */}
                            <FormField
                                control={form.control}
                                name="title"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                            <FileText className="w-4 h-4 text-blue-600" />
                                            Ticket Title
                                        </FormLabel>
                                        <FormControl>
                                            <Input
                                                placeholder="Brief summary of the issue"
                                                {...field}
                                                className="h-10 border-gray-200 focus:border-blue-500 focus:ring-blue-100 bg-gray-50/50"
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Patient */}
                                <FormField
                                    control={form.control}
                                    name="patient_id"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                                <User className="w-4 h-4 text-gray-500" />
                                                Patient
                                            </FormLabel>
                                            <Select
                                                onValueChange={field.onChange}
                                                defaultValue={field.value}
                                                disabled={isLoadingPatients}
                                            >
                                                <FormControl>
                                                    <SelectTrigger className="h-10 border-gray-200 bg-gray-50/50 focus:ring-blue-100">
                                                        <SelectValue placeholder={isLoadingPatients ? "Loading patients..." : "Select patient"} />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    {patientsData?.items?.map((patient) => (
                                                        <SelectItem key={patient.id} value={patient.id}>
                                                            {patient.first_name} {patient.last_name} {(patient.identifiers?.[0]?.value ? `(${patient.identifiers[0].value})` : '')}
                                                        </SelectItem>
                                                    ))}
                                                    {(!patientsData?.items || patientsData.items.length === 0) && (
                                                        <div className="px-2 py-2 text-sm text-gray-500 text-center">
                                                            No patients found
                                                        </div>
                                                    )}
                                                </SelectContent>
                                            </Select>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                {/* Category */}
                                <FormField
                                    control={form.control}
                                    name="category"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                                <Tag className="w-4 h-4 text-gray-500" />
                                                Category
                                            </FormLabel>
                                            <Select
                                                onValueChange={field.onChange}
                                                defaultValue={field.value}
                                            >
                                                <FormControl>
                                                    <SelectTrigger className="h-10 border-gray-200 bg-gray-50/50 focus:ring-blue-100">
                                                        <SelectValue placeholder="Select category" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    <SelectItem value="medical">Medical</SelectItem>
                                                    <SelectItem value="billing">Billing</SelectItem>
                                                    <SelectItem value="technical">Technical</SelectItem>
                                                    <SelectItem value="administrative">Administrative</SelectItem>
                                                </SelectContent>
                                            </Select>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>

                            {/* Priority */}
                            <FormField
                                control={form.control}
                                name="priority"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                            {getPriorityIcon(field.value)}
                                            Priority
                                        </FormLabel>
                                        <Select
                                            onValueChange={field.onChange}
                                            defaultValue={field.value}
                                        >
                                            <FormControl>
                                                <SelectTrigger className="h-10 border-gray-200 bg-gray-50/50 focus:ring-blue-100">
                                                    <SelectValue placeholder="Select priority" />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                <SelectItem value="low">Low</SelectItem>
                                                <SelectItem value="medium">Medium</SelectItem>
                                                <SelectItem value="high">High</SelectItem>
                                                <SelectItem value="urgent">Urgent</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            {/* Description */}
                            <FormField
                                control={form.control}
                                name="description"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                            <AlignLeft className="w-4 h-4 text-gray-500" />
                                            Description
                                        </FormLabel>
                                        <FormControl>
                                            <Textarea
                                                placeholder="Detailed description of the issue..."
                                                {...field}
                                                className="resize-none min-h-[100px] border-gray-200 focus:border-blue-500 focus:ring-blue-100 bg-gray-50/50"
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

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
                                        "Create Ticket"
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
