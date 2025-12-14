"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { TypingAnimation } from "@/components/ui/typing-animation";

// ============================================
// AI-First Interface - Typing Commands Animation
// ============================================
export function AITypingAnimation({ className }: { className?: string }) {
    const greetings = [
        "Hi! I'm your AI healthcare assistant 👋",
        "How can I help you today?",
        "Schedule appointments with natural language",
        "Just tell me what you need...",
        "I can help manage your patients!",
    ];

    return (
        <div className={cn("absolute inset-0 flex flex-col items-center justify-center p-6", className)}>
            {/* Gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-100 via-indigo-50 to-purple-100 opacity-80" />

            {/* Floating command bubbles - hidden on mobile */}
            <div className="absolute top-4 left-4 opacity-40 hidden md:block">
                <div className="bg-white/60 backdrop-blur-sm rounded-lg px-3 py-1.5 text-xs text-gray-500 shadow-sm animate-float-slow">
                    /schedule
                </div>
            </div>
            <div className="absolute top-8 right-6 opacity-30 hidden md:block">
                <div className="bg-white/60 backdrop-blur-sm rounded-lg px-3 py-1.5 text-xs text-gray-500 shadow-sm animate-float-slower">
                    /remind
                </div>
            </div>
            <div className="absolute top-16 left-1/4 opacity-25 hidden md:block">
                <div className="bg-white/60 backdrop-blur-sm rounded-lg px-3 py-1.5 text-xs text-gray-500 shadow-sm animate-float">
                    /book
                </div>
            </div>

            {/* Main typing area */}
            <div className="relative z-10 bg-white/80 backdrop-blur-md rounded-xl shadow-lg border border-white/50 p-4 w-full max-w-xs">
                <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                    <span className="text-xs font-medium text-gray-500">AI Assistant</span>
                </div>
                <div className="text-sm text-gray-700 min-h-[40px]">
                    <TypingAnimation
                        words={greetings}
                        loop={true}
                        typeSpeed={60}
                        deleteSpeed={30}
                        pauseDelay={2000}
                        className="text-sm leading-normal tracking-normal"
                        cursorStyle="line"
                    />
                </div>
            </div>
        </div>
    );
}

// ============================================
// Smart Scheduling - Animated Calendar
// ============================================
export function CalendarAnimation({ className }: { className?: string }) {
    const [activeSlot, setActiveSlot] = useState(0);

    const timeSlots = [
        { time: "9:00", patient: "John D.", type: "checkup" },
        { time: "10:30", patient: "Sarah M.", type: "follow-up" },
        { time: "11:00", patient: "Mike R.", type: "consultation" },
        { time: "2:00", patient: "Emma L.", type: "checkup" },
    ];

    useEffect(() => {
        const interval = setInterval(() => {
            setActiveSlot((prev) => (prev + 1) % timeSlots.length);
        }, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className={cn("absolute inset-0 overflow-hidden", className)}>
            {/* Gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-purple-100 via-pink-50 to-rose-100 opacity-80" />

            {/* Mini calendar widget */}
            <div className="absolute top-4 right-4 left-4 z-10">
                <div className="bg-white/80 backdrop-blur-md rounded-xl shadow-lg border border-white/50 p-3 overflow-hidden">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-semibold text-gray-700">Today's Schedule</span>
                        <span className="text-[10px] text-gray-400 font-medium">Dec 14</span>
                    </div>

                    {/* Time slots */}
                    <div className="space-y-1.5">
                        {timeSlots.map((slot, index) => (
                            <div
                                key={index}
                                className={cn(
                                    "flex items-center gap-2 p-1.5 rounded-lg transition-all duration-500",
                                    activeSlot === index
                                        ? "bg-purple-100 scale-[1.02] shadow-sm"
                                        : "bg-gray-50/50"
                                )}
                            >
                                <span className={cn(
                                    "text-[10px] font-medium w-10",
                                    activeSlot === index ? "text-purple-700" : "text-gray-400"
                                )}>
                                    {slot.time}
                                </span>
                                <div className="flex-1 min-w-0">
                                    <p className={cn(
                                        "text-[11px] font-medium truncate",
                                        activeSlot === index ? "text-purple-900" : "text-gray-600"
                                    )}>
                                        {slot.patient}
                                    </p>
                                </div>
                                <span className={cn(
                                    "text-[9px] px-1.5 py-0.5 rounded-full",
                                    activeSlot === index
                                        ? "bg-purple-200 text-purple-700"
                                        : "bg-gray-100 text-gray-500"
                                )}>
                                    {slot.type}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Decorative elements */}
            <div className="absolute bottom-4 right-4 w-16 h-16 rounded-full bg-purple-200/40 animate-pulse" />
            <div className="absolute bottom-8 right-12 w-8 h-8 rounded-full bg-pink-200/40 animate-pulse animation-delay-500" />
        </div>
    );
}

// ============================================
// Unified Comms - Chat Bubbles Animation
// ============================================
export function ChatBubblesAnimation({ className }: { className?: string }) {
    const [visibleMessages, setVisibleMessages] = useState(0);

    const messages = [
        { channel: "whatsapp", text: "Appointment confirmed for tomorrow", from: "Patient" },
        { channel: "sms", text: "Reminder: Take medication at 8 PM", from: "System" },
        { channel: "email", text: "Lab results are ready", from: "Lab" },
    ];

    useEffect(() => {
        const interval = setInterval(() => {
            setVisibleMessages((prev) => (prev + 1) % (messages.length + 2));
        }, 1500);
        return () => clearInterval(interval);
    }, []);

    const getChannelColor = (channel: string) => {
        switch (channel) {
            case "whatsapp": return "bg-green-500";
            case "sms": return "bg-blue-500";
            case "email": return "bg-orange-500";
            default: return "bg-gray-500";
        }
    };

    return (
        <div className={cn("absolute inset-0 overflow-hidden", className)}>
            {/* Gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-green-100 via-emerald-50 to-teal-100 opacity-80" />

            {/* Channel icons floating - hidden on mobile */}
            <div className="absolute top-6 right-8 opacity-60 hidden md:block">
                <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center animate-float">
                    <svg className="w-4 h-4 text-green-600" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                    </svg>
                </div>
            </div>
            <div className="absolute top-10 left-6 opacity-50 hidden md:block">
                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center animate-float-slow">
                    <svg className="w-4 h-4 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                </div>
            </div>
            <div className="absolute top-4 left-1/2 opacity-40 hidden md:block">
                <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center animate-float-slower">
                    <svg className="w-4 h-4 text-orange-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                        <polyline points="22,6 12,13 2,6" />
                    </svg>
                </div>
            </div>

            {/* Chat messages */}
            <div className="absolute top-6 md:top-20 left-4 right-4 space-y-2">
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={cn(
                            "flex items-start gap-2 transition-all duration-500 transform",
                            index <= visibleMessages
                                ? "opacity-100 translate-x-0"
                                : "opacity-0 -translate-x-4"
                        )}
                    >
                        <div className={cn("w-2 h-2 rounded-full mt-1.5 flex-shrink-0", getChannelColor(msg.channel))} />
                        <div className="bg-white/80 backdrop-blur-sm rounded-lg px-2.5 py-1.5 shadow-sm border border-white/50">
                            <p className="text-[10px] text-gray-500 mb-0.5">{msg.from}</p>
                            <p className="text-xs text-gray-700">{msg.text}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ============================================
// Secure & Compliant - Shield Animation
// ============================================
export function SecurityAnimation({ className }: { className?: string }) {
    const [checkedItems, setCheckedItems] = useState<number[]>([]);

    const securityItems = [
        "HIPAA Compliant",
        "End-to-end Encryption",
        "SOC 2 Type II",
        "Data Residency",
    ];

    useEffect(() => {
        const interval = setInterval(() => {
            setCheckedItems((prev) => {
                if (prev.length >= securityItems.length) {
                    return [];
                }
                return [...prev, prev.length];
            });
        }, 800);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className={cn("absolute inset-0 overflow-hidden", className)}>
            {/* Gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-red-100 via-orange-50 to-amber-100 opacity-80" />

            {/* Shield icon with pulse */}
            <div className="absolute top-6 left-6">
                <div className="relative">
                    <div className="absolute inset-0 w-12 h-12 bg-green-400/30 rounded-full animate-ping" />
                    <div className="relative w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center shadow-lg">
                        <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                            <polyline points="9 12 11 14 15 10" />
                        </svg>
                    </div>
                </div>
            </div>

            {/* Security checklist */}
            <div className="absolute top-6 right-4 left-20 space-y-2">
                {securityItems.map((item, index) => (
                    <div
                        key={index}
                        className={cn(
                            "flex items-center gap-2 bg-white/60 backdrop-blur-sm rounded-lg px-3 py-1.5 transition-all duration-300",
                            checkedItems.includes(index)
                                ? "shadow-sm border border-green-200/50"
                                : "border border-transparent"
                        )}
                    >
                        <div className={cn(
                            "w-4 h-4 rounded-full flex items-center justify-center transition-all duration-300",
                            checkedItems.includes(index)
                                ? "bg-green-500"
                                : "bg-gray-200"
                        )}>
                            {checkedItems.includes(index) && (
                                <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                            )}
                        </div>
                        <span className={cn(
                            "text-xs transition-colors duration-300",
                            checkedItems.includes(index)
                                ? "text-gray-800 font-medium"
                                : "text-gray-500"
                        )}>
                            {item}
                        </span>
                    </div>
                ))}
            </div>

            {/* Decorative lock icon */}
            <div className="absolute bottom-4 right-4 opacity-20">
                <svg className="w-16 h-16 text-orange-600" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 1C8.676 1 6 3.676 6 7v2H4v14h16V9h-2V7c0-3.324-2.676-6-6-6zm0 2c2.276 0 4 1.724 4 4v2H8V7c0-2.276 1.724-4 4-4zm0 10c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2z" />
                </svg>
            </div>
        </div>
    );
}
