"use client";

// Insurance Eligibility Verification Components
// EPIC-UX-009: Billing & Revenue Portal - Journey 9.1

import React, { useState, useCallback } from "react";
import { format } from "date-fns";
import {
  Shield, Check, X, RefreshCw, Loader2, AlertCircle, CreditCard,
  Download, Building2, User, Calendar, DollarSign, FileText, Printer,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { useBillingStore, type EligibilityResult, type Insurance } from "@/lib/store/billing-store";

// Eligibility Card - Shows insurance summary
interface EligibilityCardProps {
  insurance: Insurance;
  lastVerified?: string;
  onVerify: () => void;
  isVerifying?: boolean;
}

export function EligibilityCard({ insurance, lastVerified, onVerify, isVerifying }: EligibilityCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            {insurance.isPrimary ? "PRIMARY INSURANCE" : "SECONDARY INSURANCE"}
          </CardTitle>
          <Badge variant="secondary">{insurance.planType}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3">
          <Building2 className="h-5 w-5 text-primary" />
          <span className="font-medium">{insurance.payerName}</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><span className="text-muted-foreground">Member ID:</span> {insurance.memberId}</div>
          {insurance.groupNumber && <div><span className="text-muted-foreground">Group:</span> {insurance.groupNumber}</div>}
          <div><span className="text-muted-foreground">Subscriber:</span> {insurance.subscriberName} ({insurance.subscriberRelationship})</div>
        </div>
        {lastVerified && (
          <p className="text-xs text-muted-foreground">
            Last Verified: {format(new Date(lastVerified), "MMM d, yyyy")}
          </p>
        )}
        <Button onClick={onVerify} disabled={isVerifying} className="w-full">
          {isVerifying ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Verifying...</> : <><RefreshCw className="h-4 w-4 mr-2" />Verify Now</>}
        </Button>
      </CardContent>
    </Card>
  );
}

// Eligibility Result Card - Shows verification results
interface EligibilityResultCardProps {
  result: EligibilityResult;
  onSaveToRecord: () => void;
  onCollectPayment: () => void;
  onPrint: () => void;
}

export function EligibilityResultCard({ result, onSaveToRecord, onCollectPayment, onPrint }: EligibilityResultCardProps) {
  const deductibleProgress = (result.benefits.deductible.met / result.benefits.deductible.total) * 100;
  const oopProgress = (result.benefits.outOfPocketMax.met / result.benefits.outOfPocketMax.total) * 100;

  return (
    <Card className={cn("border-2", result.coverageActive ? "border-green-200 bg-green-50/50" : "border-red-200 bg-red-50/50")}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            {result.coverageActive ? <Check className="h-5 w-5 text-green-600" /> : <X className="h-5 w-5 text-red-600" />}
            {result.coverageActive ? "ELIGIBILITY VERIFIED" : "COVERAGE INACTIVE"}
          </CardTitle>
          <span className="text-xs text-muted-foreground">Just now</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Coverage Status */}
        <div className="grid grid-cols-2 gap-4 p-3 bg-background rounded-lg">
          <div><span className="text-xs text-muted-foreground">Coverage Status</span><p className="font-medium flex items-center gap-1">{result.coverageActive ? <><Check className="h-4 w-4 text-green-600" />Active</> : "Inactive"}</p></div>
          <div><span className="text-xs text-muted-foreground">Effective Date</span><p className="font-medium">{format(new Date(result.insurance.effectiveDate), "MMM d, yyyy")}</p></div>
          <div><span className="text-xs text-muted-foreground">Term Date</span><p className="font-medium">{result.insurance.termDate ? format(new Date(result.insurance.termDate), "MMM d, yyyy") : "N/A"}</p></div>
          <div><span className="text-xs text-muted-foreground">Plan Type</span><p className="font-medium">{result.insurance.planType}</p></div>
        </div>

        {/* Benefits */}
        <div className="p-3 bg-background rounded-lg space-y-3">
          <h4 className="text-xs font-medium text-muted-foreground">BENEFITS FOR: {result.serviceType || "Office Visit"}</h4>
          <div className="space-y-2">
            <div className="flex justify-between"><span>Copay:</span><span className="font-medium">₹{result.benefits.copay.toLocaleString()}</span></div>
            <div>
              <div className="flex justify-between text-sm"><span>Deductible:</span><span>₹{result.benefits.deductible.total.toLocaleString()}</span></div>
              <Progress value={deductibleProgress} className="h-2 mt-1" />
              <p className="text-xs text-muted-foreground mt-1">Met: ₹{result.benefits.deductible.met.toLocaleString()} / Remaining: ₹{result.benefits.deductible.remaining.toLocaleString()}</p>
            </div>
            <div className="flex justify-between"><span>Coinsurance:</span><span className="font-medium">{result.benefits.coinsurance}% after deductible</span></div>
            <div>
              <div className="flex justify-between text-sm"><span>Out-of-Pocket Max:</span><span>₹{result.benefits.outOfPocketMax.total.toLocaleString()}</span></div>
              <Progress value={oopProgress} className="h-2 mt-1" />
              <p className="text-xs text-muted-foreground mt-1">Met: ₹{result.benefits.outOfPocketMax.met.toLocaleString()}</p>
            </div>
            <div className="flex justify-between"><span>Prior Auth Required:</span><Badge variant={result.benefits.priorAuthRequired ? "destructive" : "secondary"}>{result.benefits.priorAuthRequired ? "Yes" : "No"}</Badge></div>
          </div>
        </div>

        {/* Collect Today */}
        <div className="p-4 bg-primary/10 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-primary" />
            <span className="font-medium">COLLECT TODAY:</span>
          </div>
          <span className="text-xl font-bold text-primary">₹{result.collectToday.toLocaleString()}</span>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onSaveToRecord}><Download className="h-4 w-4 mr-1" />Save to Record</Button>
          <Button size="sm" onClick={onCollectPayment}><CreditCard className="h-4 w-4 mr-1" />Collect Payment</Button>
          <Button variant="outline" size="sm" onClick={onPrint}><Printer className="h-4 w-4 mr-1" />Print</Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Main Eligibility Verification Component
interface EligibilityVerificationProps {
  patientId: string;
  patientName: string;
  insurance: Insurance;
  onCollectPayment: (amount: number) => void;
}

export function EligibilityVerification({ patientId, patientName, insurance, onCollectPayment }: EligibilityVerificationProps) {
  const { verifyEligibility, currentEligibility, isVerifyingEligibility } = useBillingStore();

  const handleVerify = useCallback(async () => {
    await verifyEligibility(patientId, insurance.id, "Office Visit (99213)");
  }, [verifyEligibility, patientId, insurance.id]);

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Insurance Eligibility
          </h2>
          <p className="text-sm text-muted-foreground">Patient: {patientName}</p>
        </div>
      </div>

      <EligibilityCard insurance={insurance} onVerify={handleVerify} isVerifying={isVerifyingEligibility} />

      {currentEligibility && (
        <EligibilityResultCard
          result={currentEligibility}
          onSaveToRecord={() => {}}
          onCollectPayment={() => onCollectPayment(currentEligibility.collectToday)}
          onPrint={() => window.print()}
        />
      )}
    </div>
  );
}

export default EligibilityVerification;
