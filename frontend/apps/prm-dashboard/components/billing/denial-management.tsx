"use client";

// Denial Management Components
// EPIC-UX-009: Billing & Revenue Portal - Journey 9.3

import React, { useEffect, useState } from "react";
import { format, differenceInDays } from "date-fns";
import { AlertTriangle, Sparkles, Check, X, Clock, ChevronRight, RefreshCw, Eye, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useBillingStore, type Denial } from "@/lib/store/billing-store";

// AI Analysis Card
interface AIAnalysisCardProps {
  analysis: { issueIdentified: string; suggestedAction: string; successProbability: number };
  onApplyFix: () => void;
  onViewSimilar: () => void;
  onEscalate: () => void;
  isApplying?: boolean;
}

export function AIAnalysisCard({ analysis, onApplyFix, onViewSimilar, onEscalate, isApplying }: AIAnalysisCardProps) {
  return (
    <Card className="border-purple-200 bg-purple-50/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2"><Sparkles className="h-4 w-4 text-purple-600" />AI ANALYSIS & RECOMMENDATION</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-xs font-medium text-purple-700">Issue Identified:</p>
          <p className="text-sm mt-1">{analysis.issueIdentified}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-purple-700">Suggested Action:</p>
          <p className="text-sm mt-1">{analysis.suggestedAction}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Success Probability:</span>
          <Progress value={analysis.successProbability} className="flex-1 h-2" />
          <Badge variant="secondary" className="bg-green-100 text-green-700">{analysis.successProbability}%</Badge>
        </div>
        <div className="flex gap-2">
          <Button size="sm" onClick={onApplyFix} disabled={isApplying}>
            {isApplying ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Check className="h-4 w-4 mr-1" />}
            Apply Fix & Resubmit
          </Button>
          <Button variant="outline" size="sm" onClick={onViewSimilar}>View Similar</Button>
          <Button variant="ghost" size="sm" onClick={onEscalate}>Escalate</Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Denial Card
interface DenialCardProps {
  denial: Denial;
  onView: () => void;
  onApplyFix: () => void;
}

export function DenialCard({ denial, onView, onApplyFix }: DenialCardProps) {
  const urgencyColor = denial.daysRemaining < 14 ? "text-red-600" : denial.daysRemaining < 30 ? "text-amber-600" : "text-muted-foreground";

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={onView}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <span className="font-medium">{denial.claim.claimNumber}</span>
              <Badge variant="secondary" className="text-xs">{denial.denialCode}</Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{denial.claim.patientName} • {denial.claim.insurance.payerName}</p>
            <p className="text-sm mt-2">{denial.denialReason}</p>
            <div className="flex items-center gap-4 mt-2 text-xs">
              <span className={urgencyColor}><Clock className="h-3 w-3 inline mr-1" />{denial.daysRemaining} days to appeal</span>
              <span>₹{denial.claim.totalCharged.toLocaleString()}</span>
            </div>
          </div>
          {denial.aiAnalysis && (
            <Badge variant="secondary" className="bg-purple-100 text-purple-700 text-xs">
              <Sparkles className="h-3 w-3 mr-1" />{denial.aiAnalysis.successProbability}% fix rate
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Denial Detail View
interface DenialDetailViewProps {
  denial: Denial;
  onClose: () => void;
  onApplyFix: () => void;
  onAppeal: (notes: string) => void;
}

export function DenialDetailView({ denial, onClose, onApplyFix, onAppeal }: DenialDetailViewProps) {
  const [isApplying, setIsApplying] = useState(false);

  const handleApplyFix = async () => {
    setIsApplying(true);
    await onApplyFix();
    setIsApplying(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Denied Claim: {denial.claim.claimNumber}</h2>
        <Button variant="ghost" size="icon" onClick={onClose}><X className="h-4 w-4" /></Button>
      </div>

      {/* Denial Details */}
      <Card className="border-red-200 bg-red-50/50">
        <CardHeader className="pb-2"><CardTitle className="text-sm text-red-800">🔴 DENIAL DETAILS</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="grid grid-cols-2 gap-2">
            <div><span className="text-muted-foreground">Patient:</span> {denial.claim.patientName}</div>
            <div><span className="text-muted-foreground">DOS:</span> {format(new Date(denial.claim.dateOfService), "MMM d, yyyy")}</div>
            <div><span className="text-muted-foreground">Payer:</span> {denial.claim.insurance.payerName}</div>
            <div><span className="text-muted-foreground">Billed:</span> ₹{denial.claim.totalCharged.toLocaleString()}</div>
          </div>
          <div className="pt-2 border-t">
            <p><span className="font-medium">Denial Code:</span> {denial.denialCode}</p>
            <p className="mt-1"><span className="font-medium">Reason:</span> {denial.denialReason}</p>
            <p className="mt-2 text-amber-700"><span className="font-medium">Appeal Deadline:</span> {format(new Date(denial.appealDeadline), "MMM d, yyyy")} ({denial.daysRemaining} days)</p>
          </div>
        </CardContent>
      </Card>

      {/* AI Analysis */}
      {denial.aiAnalysis && (
        <AIAnalysisCard
          analysis={denial.aiAnalysis}
          onApplyFix={handleApplyFix}
          onViewSimilar={() => {}}
          onEscalate={() => {}}
          isApplying={isApplying}
        />
      )}

      {/* Line Items */}
      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm">CLAIM LINE ITEMS</CardTitle></CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr><th className="text-left p-2">Line</th><th className="text-left p-2">CPT</th><th className="text-left p-2">Description</th><th className="text-left p-2">Modifier</th><th className="text-right p-2">Billed</th><th className="p-2">Status</th></tr>
            </thead>
            <tbody>
              {denial.claim.lineItems.map((item, i) => (
                <tr key={item.id} className="border-t">
                  <td className="p-2">{i + 1}</td>
                  <td className="p-2 font-medium">{item.cptCode}</td>
                  <td className="p-2">{item.description}</td>
                  <td className="p-2">{item.modifiers.length > 0 ? item.modifiers.join(", ") : <span className="text-amber-600">⚠️ Add 25</span>}</td>
                  <td className="p-2 text-right">₹{item.chargeAmount.toLocaleString()}</td>
                  <td className="p-2">{item.status === "denied" ? "🔴" : "🟢"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

// Main Denial Management Component
export function DenialManagement() {
  const [selectedDenial, setSelectedDenial] = useState<Denial | null>(null);
  const { denials, isLoadingDenials, fetchDenials, applyDenialFix, appealDenial } = useBillingStore();

  useEffect(() => { fetchDenials(); }, [fetchDenials]);

  if (selectedDenial) {
    return (
      <DenialDetailView
        denial={selectedDenial}
        onClose={() => setSelectedDenial(null)}
        onApplyFix={() => applyDenialFix(selectedDenial.id)}
        onAppeal={(notes) => appealDenial(selectedDenial.id, notes)}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2"><AlertTriangle className="h-6 w-6 text-red-600" />Denial Management</h1>
        <Badge variant="destructive">{denials.length} Denials</Badge>
      </div>

      {isLoadingDenials ? (
        <div className="text-center py-8"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></div>
      ) : denials.length === 0 ? (
        <Card><CardContent className="py-8 text-center text-muted-foreground">No denials to work</CardContent></Card>
      ) : (
        <div className="space-y-3">
          {denials.map((denial) => (
            <DenialCard
              key={denial.id}
              denial={denial}
              onView={() => setSelectedDenial(denial)}
              onApplyFix={() => applyDenialFix(denial.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default DenialManagement;
