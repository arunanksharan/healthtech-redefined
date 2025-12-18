"use client";

import * as React from "react";
import { CreditCard, Clock, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";

export default function BillingPage() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] p-6">
            <Card className="w-full max-w-lg bg-white dark:bg-gray-800 border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-lg">
                <CardContent className="flex flex-col items-center justify-center py-16 px-8 text-center">
                    {/* Flat Icon */}
                    <div className="relative mb-6">
                        <div className="w-20 h-20 rounded-lg bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800 flex items-center justify-center">
                            <CreditCard className="w-10 h-10 text-blue-500" />
                        </div>
                    </div>

                    {/* Badge */}
                    <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-50 dark:bg-amber-900/20 border-2 border-amber-200 dark:border-amber-800 mb-4">
                        <Clock className="w-4 h-4 text-amber-500" />
                        <span className="text-sm font-medium text-amber-600 dark:text-amber-400">
                            Coming Soon
                        </span>
                    </div>

                    {/* Title */}
                    <h1 className="text-2xl font-heading text-gray-900 dark:text-white mb-2">Billing & Insurance</h1>

                    {/* Description */}
                    <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-sm">
                        Comprehensive billing management, insurance claims processing, and payment tracking is currently under development.
                    </p>

                    {/* Features Preview */}
                    <div className="grid grid-cols-2 gap-3 text-sm text-gray-500 dark:text-gray-400 mb-8">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-blue-500" />
                            Payment Processing
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-blue-500" />
                            Claims Management
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-blue-500" />
                            Insurance Verification
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-blue-500" />
                            Statement Generation
                        </div>
                    </div>

                    {/* Back Button */}
                    <Link href="/dashboard">
                        <Button variant="outline" className="gap-2 border-2 border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg">
                            <ArrowLeft className="w-4 h-4" />
                            Back to Dashboard
                        </Button>
                    </Link>
                </CardContent>
            </Card>
        </div>
    );
}

