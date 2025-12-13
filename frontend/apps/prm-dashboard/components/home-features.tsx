"use client";

import { cn } from "@/lib/utils";
import { Marquee } from "@/components/ui/marquee";
import { AnimatedList } from "@/components/ui/animated-list";
import { Calendar } from "@/components/ui/calendar";
import {
    MessageCircle,
    Mail,
    Smartphone,
    Slack,
    Linkedin,
    Chrome
} from "lucide-react";

// --- Integrations Marquee ---

const integrations = [
    {
        name: "WhatsApp",
        icon: <MessageCircle className="h-6 w-6 text-green-500" />,
        color: "bg-green-50 border-green-100",
    },
    {
        name: "Email",
        icon: <Mail className="h-6 w-6 text-blue-500" />,
        color: "bg-blue-50 border-blue-100",
    },
    {
        name: "SMS",
        icon: <Smartphone className="h-6 w-6 text-purple-500" />,
        color: "bg-purple-50 border-purple-100",
    },
    {
        name: "Slack",
        icon: <Slack className="h-6 w-6 text-orange-500" />,
        color: "bg-orange-50 border-orange-100",
    },
    {
        name: "LinkedIn",
        icon: <Linkedin className="h-6 w-6 text-blue-700" />,
        color: "bg-blue-50 border-blue-200",
    },
];

export function IntegrationsMarquee() {
    return (
        <div className="relative flex h-full w-full flex-col items-center justify-center overflow-hidden rounded-lg bg-background p-4">
            <Marquee pauseOnHover className="[--duration:20s]">
                {integrations.map((item, idx) => (
                    <div
                        key={idx}
                        className={cn(
                            "flex flex-row items-center gap-2 rounded-xl border p-3",
                            "bg-white dark:bg-gray-800",
                            item.color
                        )}
                    >
                        {item.icon}
                        <span className="text-sm font-medium">{item.name}</span>
                    </div>
                ))}
            </Marquee>
            <Marquee reverse pauseOnHover className="[--duration:20s] mt-4">
                {integrations.map((item, idx) => (
                    <div
                        key={idx}
                        className={cn(
                            "flex flex-row items-center gap-2 rounded-xl border p-3",
                            "bg-white dark:bg-gray-800",
                            item.color
                        )}
                    >
                        {item.icon}
                        <span className="text-sm font-medium">{item.name}</span>
                    </div>
                ))}
            </Marquee>
            <div className="pointer-events-none absolute inset-y-0 left-0 w-1/3 bg-gradient-to-r from-white dark:from-background"></div>
            <div className="pointer-events-none absolute inset-y-0 right-0 w-1/3 bg-gradient-to-l from-white dark:from-background"></div>
        </div>
    );
}

// --- Conversation List ---

interface Item {
    name: string;
    description: string;
    icon: string;
    color: string;
    time: string;
}

let notifications = [
    {
        name: "Dr. Smith",
        description: "Referral sent for patient John Doe.",
        time: "2m ago",
        icon: "👨‍⚕️",
        color: "#00C9A7",
    },
    {
        name: "System",
        description: "Appointment reschedule confirmed.",
        time: "5m ago",
        icon: "📅",
        color: "#FFB800",
    },
    {
        name: "Sarah (AI)",
        description: "Patient insurance verified.",
        time: "10m ago",
        icon: "🤖",
        color: "#FF3D71",
    },
    {
        name: "Lab Results",
        description: "Blood work analysis complete.",
        time: "15m ago",
        icon: "🩸",
        color: "#1E86FF",
    },
];

notifications = Array.from({ length: 10 }, () => notifications).flat();

const Notification = ({ name, description, icon, color, time }: Item) => {
    return (
        <figure
            className={cn(
                "relative mx-auto min-h-fit w-full max-w-[400px] cursor-pointer overflow-hidden rounded-2xl p-4",
                // animation styles
                "transition-all duration-200 ease-in-out hover:scale-[103%]",
                // light styles
                "bg-white [box-shadow:0_0_0_1px_rgba(0,0,0,.03),0_2px_4px_rgba(0,0,0,.05),0_12px_24px_rgba(0,0,0,.05)]",
                // dark styles
                "transform-gpu dark:bg-transparent dark:backdrop-blur-md dark:[border:1px_solid_rgba(255,255,255,.1)] dark:[box-shadow:0_-20px_80px_-20px_#ffffff1f_inset]",
            )}
        >
            <div className="flex flex-row items-center gap-3">
                <div
                    className="flex h-10 w-10 items-center justify-center rounded-2xl"
                    style={{
                        backgroundColor: color,
                    }}
                >
                    <span className="text-lg">{icon}</span>
                </div>
                <div className="flex flex-col overflow-hidden">
                    <figcaption className="flex flex-row items-center whitespace-pre text-lg font-medium dark:text-white ">
                        <span className="text-sm sm:text-lg">{name}</span>
                        <span className="mx-1">·</span>
                        <span className="text-xs text-gray-500">{time}</span>
                    </figcaption>
                    <p className="text-sm font-normal dark:text-white/60">
                        {description}
                    </p>
                </div>
            </div>
        </figure>
    );
};

export function ConversationList() {
    return (
        <div className="relative flex h-full max-h-[300px] w-full flex-col overflow-hidden rounded-lg bg-background p-6">
            <AnimatedList>
                {notifications.map((item, idx) => (
                    <Notification key={idx} {...item} />
                ))}
            </AnimatedList>
            <div className="pointer-events-none absolute inset-x-0 bottom-0 h-1/4 bg-gradient-to-t from-background"></div>
        </div>
    );
}


// --- Calendar Demo ---

export function CalendarDemo() {
    return (
        <div className="flex h-full w-full items-center justify-center bg-background p-4">
            <Calendar
                mode="single"
                selected={new Date()}
                className="rounded-md border shadow scale-90"
            />
        </div>
    )
}
