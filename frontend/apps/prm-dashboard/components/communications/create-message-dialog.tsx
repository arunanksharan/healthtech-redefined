"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
    MessageSquare,
    User,
    Mail,
    Smartphone,
    MessageCircle,
    Send,
    FileText,
    Sparkles
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
    FormDescription,
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
import { communicationsAPI } from "@/lib/api/communications";
import toast from "react-hot-toast";
import { cn } from "@/lib/utils/cn";

const formSchema = z.object({
    patient_id: z.string().min(1, { message: "Please select a patient." }),
    channel: z.enum(["whatsapp", "sms", "email"]),
    recipient: z.string().min(1, { message: "Recipient is required." }),
    subject: z.string().optional(),
    message: z.string().min(5, { message: "Message must be at least 5 characters." }),
    template_id: z.string().optional(),
});

interface CreateMessageDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function CreateMessageDialog({
    open,
    onOpenChange,
    onSuccess,
}: CreateMessageDialogProps) {
    const [loading, setLoading] = useState(false);

    // Mock templates
    const templates = [
        { id: "appt_reminder", name: "Appointment Reminder", content: "Hi {{patient_name}}, this is a reminder for your appointment tomorrow at 10 AM." },
        { id: "welcome", name: "Welcome Message", content: "Welcome to our clinic, {{patient_name}}! We are here to support your health journey." },
        { id: "follow_up", name: "Post-Visit Follow Up", content: "Hi {{patient_name}}, checking in to see how you are feeling after your visit." },
    ];

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            patient_id: "",
            channel: "whatsapp",
            recipient: "",
            subject: "",
            message: "",
            template_id: "none",
        },
    });

    // Auto-fill recipient based on mocked patient data
    // In real app, this would fetch patient details
    const watchPatient = form.watch("patient_id");
    const watchChannel = form.watch("channel");
    const watchTemplate = form.watch("template_id");

    useEffect(() => {
        if (watchPatient) {
            // Mock data mapping
            const mockContact = {
                "p1": { phone: "+15550001", email: "john@example.com" },
                "p2": { phone: "+15550002", email: "jane@example.com" },
                "p3": { phone: "+15550003", email: "robert@example.com" },
            }[watchPatient] || { phone: "", email: "" };

            if (watchChannel === "email") {
                form.setValue("recipient", mockContact.email);
            } else {
                form.setValue("recipient", mockContact.phone);
            }
        }
    }, [watchPatient, watchChannel, form]);

    useEffect(() => {
        if (watchTemplate && watchTemplate !== "none") {
            const template = templates.find(t => t.id === watchTemplate);
            if (template) {
                form.setValue("message", template.content);
                if (watchChannel === "email" && !form.getValues("subject")) {
                    form.setValue("subject", template.name);
                }
            }
        }
    }, [watchTemplate, form, watchChannel]);

    async function onSubmit(values: z.infer<typeof formSchema>) {
        setLoading(true);
        try {
            let error = null;
            let data = null;

            if (values.channel === 'whatsapp') {
                [data, error] = await communicationsAPI.sendWhatsApp({
                    patient_id: values.patient_id,
                    message: values.message,
                    // template_id: values.template_id !== 'none' ? values.template_id : undefined
                });
            } else if (values.channel === 'sms') {
                [data, error] = await communicationsAPI.sendSMS({
                    patient_id: values.patient_id,
                    message: values.message,
                    phone_number: values.recipient,
                });
            } else if (values.channel === 'email') {
                [data, error] = await communicationsAPI.sendEmail({
                    patient_id: values.patient_id,
                    subject: values.subject || "New Message",
                    body: values.message,
                    email_address: values.recipient,
                });
            }

            if (error) {
                toast.error(error.message || "Failed to send message");
                return;
            }

            toast.success(`Message sent via ${values.channel}`);
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

    const getChannelIcon = (channel: string) => {
        switch (channel) {
            case 'whatsapp': return <MessageCircle className="w-4 h-4 text-green-500" />;
            case 'sms': return <Smartphone className="w-4 h-4 text-blue-500" />;
            case 'email': return <Mail className="w-4 h-4 text-purple-500" />;
            default: return <MessageSquare className="w-4 h-4 text-gray-500" />;
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] p-0 overflow-hidden border-0 shadow-2xl">
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
                    <DialogHeader>
                        <DialogTitle className="text-xl font-bold flex items-center gap-2">
                            <Send className="w-5 h-5 text-blue-100" />
                            New Message
                        </DialogTitle>
                        <DialogDescription className="text-blue-100/90 text-sm">
                            Send a direct message, alert, or notification to a patient.
                        </DialogDescription>
                    </DialogHeader>
                </div>

                <div className="p-6 bg-white dark:bg-zinc-950">
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Patient */}
                                <FormField
                                    control={form.control}
                                    name="patient_id"
                                    render={({ field }) => (
                                        <FormItem className="col-span-2 md:col-span-1">
                                            <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                                <User className="w-4 h-4 text-gray-500" />
                                                Patient
                                            </FormLabel>
                                            <Select
                                                onValueChange={field.onChange}
                                                defaultValue={field.value}
                                            >
                                                <FormControl>
                                                    <SelectTrigger className="h-10 border-gray-200 bg-gray-50/50 focus:ring-blue-100">
                                                        <SelectValue placeholder="Select patient" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    <SelectItem value="p1">John Doe (MRN001)</SelectItem>
                                                    <SelectItem value="p2">Jane Smith (MRN002)</SelectItem>
                                                    <SelectItem value="p3">Robert Johnson (MRN003)</SelectItem>
                                                </SelectContent>
                                            </Select>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                {/* Channel */}
                                <FormField
                                    control={form.control}
                                    name="channel"
                                    render={({ field }) => (
                                        <FormItem className="col-span-2 md:col-span-1">
                                            <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                                {getChannelIcon(field.value)}
                                                Channel
                                            </FormLabel>
                                            <Select
                                                onValueChange={field.onChange}
                                                defaultValue={field.value}
                                            >
                                                <FormControl>
                                                    <SelectTrigger className="h-10 border-gray-200 bg-gray-50/50 focus:ring-blue-100">
                                                        <SelectValue placeholder="Select channel" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                                                    <SelectItem value="sms">SMS</SelectItem>
                                                    <SelectItem value="email">Email</SelectItem>
                                                </SelectContent>
                                            </Select>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>

                            {/* Recipient Input (Auto-filled) */}
                            <FormField
                                control={form.control}
                                name="recipient"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                            <Smartphone className="w-4 h-4 text-gray-500" />
                                            Recipient {watchChannel === 'email' ? 'Email' : 'Number'}
                                        </FormLabel>
                                        <FormControl>
                                            <Input
                                                placeholder={watchChannel === 'email' ? "name@example.com" : "+1234567890"}
                                                {...field}
                                                className="h-10 border-gray-200 focus:border-blue-500 focus:ring-blue-100 bg-gray-50/50"
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            {/* Subject (Email Only) */}
                            {watchChannel === 'email' && (
                                <FormField
                                    control={form.control}
                                    name="subject"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                                <FileText className="w-4 h-4 text-gray-500" />
                                                Subject
                                            </FormLabel>
                                            <FormControl>
                                                <Input
                                                    placeholder="Message subject"
                                                    {...field}
                                                    className="h-10 border-gray-200 focus:border-blue-500 focus:ring-blue-100 bg-gray-50/50"
                                                />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            )}

                            {/* Template Selector */}
                            <FormField
                                control={form.control}
                                name="template_id"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                            <Sparkles className="w-4 h-4 text-amber-500" />
                                            Use Template (Optional)
                                        </FormLabel>
                                        <Select
                                            onValueChange={field.onChange}
                                            defaultValue={field.value}
                                        >
                                            <FormControl>
                                                <SelectTrigger className="h-10 border-gray-200 bg-gray-50/50 focus:ring-blue-100">
                                                    <SelectValue placeholder="Select a template" />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                <SelectItem value="none">None</SelectItem>
                                                {templates.map(t => (
                                                    <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            {/* Message Body */}
                            <FormField
                                control={form.control}
                                name="message"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-gray-700 font-semibold flex items-center gap-2">
                                            <FileText className="w-4 h-4 text-gray-500" />
                                            Message
                                        </FormLabel>
                                        <FormControl>
                                            <Textarea
                                                placeholder="Type your message here..."
                                                {...field}
                                                className="resize-none min-h-[120px] border-gray-200 focus:border-blue-500 focus:ring-blue-100 bg-gray-50/50 font-sans"
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
                                            Sending...
                                        </>
                                    ) : (
                                        "Send Message"
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
