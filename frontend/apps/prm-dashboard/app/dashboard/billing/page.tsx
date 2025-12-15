"use client";

import * as React from "react";
import { CreditCard, Clock, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";

export default function BillingPage() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] p-6">
            <Card className="w-full max-w-lg bg-gradient-to-br from-background to-muted/30 border-2 border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-16 px-8 text-center">
                    {/* Icon */}
                    <div className="relative mb-6">
                        <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl animate-pulse" />
                        <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                            <CreditCard className="w-10 h-10 text-primary" />
                        </div>
                    </div>

                    {/* Badge */}
                    <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20 mb-4">
                        <Clock className="w-4 h-4 text-amber-500" />
                        <span className="text-sm font-medium text-amber-600 dark:text-amber-400">
                            Coming Soon
                        </span>
                    </div>

                    {/* Title */}
                    <h1 className="text-2xl font-bold mb-2">Billing & Insurance</h1>

                    {/* Description */}
                    <p className="text-muted-foreground mb-6 max-w-sm">
                        Comprehensive billing management, insurance claims processing, and payment tracking is currently under development.
                    </p>

                    {/* Features Preview */}
                    <div className="grid grid-cols-2 gap-3 text-sm text-muted-foreground mb-8">
                        <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-primary/60" />
                            Payment Processing
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-primary/60" />
                            Claims Management
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-primary/60" />
                            Insurance Verification
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-primary/60" />
                            Statement Generation
                        </div>
                    </div>

                    {/* Back Button */}
                    <Link href="/dashboard">
                        <Button variant="outline" className="gap-2">
                            <ArrowLeft className="w-4 h-4" />
                            Back to Dashboard
                        </Button>
                    </Link>
                </CardContent>
            </Card>
        </div>
    );
}
