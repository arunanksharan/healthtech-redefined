"use client";

// Revenue Analytics Dashboard
// EPIC-UX-009: Billing & Revenue Portal - Journey 9.5

import React, { useEffect } from "react";
import { TrendingUp, TrendingDown, DollarSign, Clock, AlertTriangle, Download, Calendar, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useBillingStore, type RevenueMetrics } from "@/lib/store/billing-store";

// Revenue Metrics Cards
export function RevenueMetricsCards({ metrics }: { metrics: RevenueMetrics }) {
  const cards = [
    { label: "GROSS REVENUE", value: `₹${(metrics.grossRevenue / 10000000).toFixed(2)} Cr`, trend: "+12% MoM", positive: true, icon: DollarSign },
    { label: "NET REVENUE", value: `₹${(metrics.netRevenue / 100000).toFixed(1)}L`, trend: "+8% MoM", positive: true, icon: DollarSign },
    { label: "COLLECTIONS", value: `${metrics.collectionRate}%`, trend: "+2.1%", positive: true, icon: TrendingUp },
    { label: "DAYS IN AR", value: `${metrics.daysInAR} days`, trend: "-3 days", positive: true, icon: Clock },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map((card) => (
        <Card key={card.label}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">{card.label}</span>
              <card.icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold">{card.value}</p>
            <p className={cn("text-xs flex items-center gap-1", card.positive ? "text-green-600" : "text-red-600")}>
              {card.positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {card.trend}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Revenue by Department Chart
export function RevenueDepartmentChart({ data }: { data: RevenueMetrics["byDepartment"] }) {
  const maxAmount = Math.max(...data.map((d) => d.amount));

  return (
    <Card>
      <CardHeader className="pb-2"><CardTitle className="text-sm">REVENUE BY DEPARTMENT</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {data.map((dept) => (
          <div key={dept.name} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span>{dept.name}</span>
              <span className="text-muted-foreground">₹{(dept.amount / 100000).toFixed(1)}L ({dept.percentage}%)</span>
            </div>
            <Progress value={(dept.amount / maxAmount) * 100} className="h-2" />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// AR Aging Chart
export function ARAgingChart({ data }: { data: RevenueMetrics["arAging"] }) {
  const total = data.reduce((sum, d) => sum + d.amount, 0);
  const colors = ["bg-green-500", "bg-yellow-500", "bg-orange-500", "bg-red-500"];

  return (
    <Card>
      <CardHeader className="pb-2"><CardTitle className="text-sm">AR AGING</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {data.map((bucket, i) => (
          <div key={bucket.bucket} className="flex items-center gap-3">
            <div className={cn("w-3 h-3 rounded-full", colors[i])} />
            <span className="flex-1 text-sm">{bucket.bucket}</span>
            <span className="text-sm font-medium">₹{(bucket.amount / 100000).toFixed(1)}L</span>
          </div>
        ))}
        <div className="pt-2 border-t flex justify-between font-medium">
          <span>Total AR</span>
          <span>₹{(total / 100000).toFixed(1)}L</span>
        </div>
      </CardContent>
    </Card>
  );
}

// Denial Rate by Payer
function DenialRateChart({ data }: { data: RevenueMetrics["byPayer"] }) {
  return (
    <Card>
      <CardHeader className="pb-2"><CardTitle className="text-sm">DENIAL RATE BY PAYER</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {data.map((payer) => (
          <div key={payer.name} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span>{payer.name}</span>
              <span className={cn(payer.denialRate > 10 ? "text-red-600" : payer.denialRate > 5 ? "text-amber-600" : "text-green-600")}>
                {payer.denialRate}%
              </span>
            </div>
            <Progress value={payer.denialRate} className="h-2" />
          </div>
        ))}
        <div className="pt-2 border-t">
          <p className="text-sm">Avg: <span className="font-medium">7.4%</span> <span className="text-green-600 text-xs">↓ 1.2% better</span></p>
        </div>
      </CardContent>
    </Card>
  );
}

// Main Revenue Analytics Component
export function RevenueAnalytics() {
  const [period, setPeriod] = React.useState("november-2024");
  const { revenueMetrics, isLoadingMetrics, fetchRevenueMetrics } = useBillingStore();

  useEffect(() => { fetchRevenueMetrics(period); }, [fetchRevenueMetrics, period]);

  if (isLoadingMetrics || !revenueMetrics) {
    return <div className="space-y-6 animate-pulse">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-32 bg-muted rounded-lg" />)}</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2"><BarChart3 className="h-6 w-6" />Revenue Analytics</h1>
          <p className="text-sm text-muted-foreground">{revenueMetrics.period}</p>
        </div>
        <div className="flex gap-2">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="november-2024">November 2024</SelectItem>
              <SelectItem value="october-2024">October 2024</SelectItem>
              <SelectItem value="q4-2024">Q4 2024</SelectItem>
              <SelectItem value="ytd-2024">YTD 2024</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Report</Button>
          <Button variant="outline"><Calendar className="h-4 w-4 mr-2" />Compare Periods</Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <RevenueMetricsCards metrics={revenueMetrics} />

      {/* Charts Grid */}
      <div className="grid grid-cols-2 gap-6">
        <RevenueDepartmentChart data={revenueMetrics.byDepartment} />
        <div className="space-y-6">
          <DenialRateChart data={revenueMetrics.byPayer} />
          <ARAgingChart data={revenueMetrics.arAging} />
        </div>
      </div>

      {/* Trend Chart Placeholder */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">REVENUE TREND (12 MONTHS)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-end gap-2">
            {revenueMetrics.trend.map((point, i) => {
              const height = (point.revenue / 10000000) * 100;
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: `${height}%` }}>
                    <div className="w-full bg-primary rounded-t" style={{ height: `${(point.collections / point.revenue) * 100}%` }} />
                  </div>
                  <span className="text-[10px] text-muted-foreground">{point.date.split("-")[1]}</span>
                </div>
              );
            })}
          </div>
          <div className="flex gap-4 mt-4 text-xs">
            <div className="flex items-center gap-2"><div className="w-3 h-3 bg-primary rounded" /><span>Collections</span></div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 bg-primary/20 rounded" /><span>Revenue</span></div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default RevenueAnalytics;
