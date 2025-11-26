"use client";

// Patient Billing Statement & Payment Components
// EPIC-UX-009: Billing & Revenue Portal - Journey 9.4

import React, { useState } from "react";
import { format } from "date-fns";
import { CreditCard, DollarSign, Download, MessageSquare, Calendar, Check, Loader2, Building2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { useBillingStore, type Statement, type Payment } from "@/lib/store/billing-store";

// Payment Form
interface PaymentFormProps {
  amount: number;
  onSubmit: (method: string, amount: number) => Promise<void>;
  onCancel: () => void;
}

export function PaymentForm({ amount, onSubmit, onCancel }: PaymentFormProps) {
  const [method, setMethod] = useState("card");
  const [payAmount, setPayAmount] = useState(amount);
  const [isProcessing, setIsProcessing] = useState(false);
  const [cardNumber, setCardNumber] = useState("");
  const [expiry, setExpiry] = useState("");
  const [cvv, setCvv] = useState("");

  const handleSubmit = async () => {
    setIsProcessing(true);
    try {
      await onSubmit(method, payAmount);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center p-4 bg-primary/10 rounded-lg">
        <p className="text-sm text-muted-foreground">Amount to Pay</p>
        <p className="text-3xl font-bold text-primary">₹{payAmount.toLocaleString()}</p>
      </div>

      <div className="space-y-4">
        <Label>Payment Method</Label>
        <RadioGroup value={method} onValueChange={setMethod} className="space-y-2">
          <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-muted/50">
            <RadioGroupItem value="card" id="card" />
            <Label htmlFor="card" className="flex-1 cursor-pointer">Credit/Debit Card</Label>
            <CreditCard className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-muted/50">
            <RadioGroupItem value="upi" id="upi" />
            <Label htmlFor="upi" className="flex-1 cursor-pointer">UPI</Label>
          </div>
          <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-muted/50">
            <RadioGroupItem value="netbanking" id="netbanking" />
            <Label htmlFor="netbanking" className="flex-1 cursor-pointer">Net Banking</Label>
          </div>
        </RadioGroup>
      </div>

      {method === "card" && (
        <div className="space-y-4">
          <div><Label>Card Number</Label><Input placeholder="1234 5678 9012 3456" value={cardNumber} onChange={(e) => setCardNumber(e.target.value)} /></div>
          <div className="grid grid-cols-2 gap-4">
            <div><Label>Expiry</Label><Input placeholder="MM/YY" value={expiry} onChange={(e) => setExpiry(e.target.value)} /></div>
            <div><Label>CVV</Label><Input placeholder="123" type="password" value={cvv} onChange={(e) => setCvv(e.target.value)} /></div>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <Button variant="outline" className="flex-1" onClick={onCancel}>Cancel</Button>
        <Button className="flex-1" onClick={handleSubmit} disabled={isProcessing}>
          {isProcessing ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Processing...</> : <>Pay ₹{payAmount.toLocaleString()}</>}
        </Button>
      </div>
    </div>
  );
}

// Payment Plan Dialog
interface PaymentPlanDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  totalAmount: number;
  onSetup: (months: number) => void;
}

export function PaymentPlanDialog({ open, onOpenChange, totalAmount, onSetup }: PaymentPlanDialogProps) {
  const [months, setMonths] = useState(3);
  const monthlyAmount = Math.ceil(totalAmount / months);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>Set Up Payment Plan</DialogTitle></DialogHeader>
        <div className="space-y-4 py-4">
          <div className="text-center p-4 bg-muted rounded-lg">
            <p className="text-sm text-muted-foreground">Total Balance</p>
            <p className="text-2xl font-bold">₹{totalAmount.toLocaleString()}</p>
          </div>
          <div className="space-y-2">
            <Label>Number of Payments</Label>
            <RadioGroup value={String(months)} onValueChange={(v) => setMonths(Number(v))} className="grid grid-cols-3 gap-2">
              {[3, 6, 12].map((m) => (
                <div key={m} className={cn("p-3 border rounded-lg text-center cursor-pointer", months === m && "border-primary bg-primary/5")}>
                  <RadioGroupItem value={String(m)} id={`m-${m}`} className="sr-only" />
                  <Label htmlFor={`m-${m}`} className="cursor-pointer">
                    <p className="font-medium">{m} months</p>
                    <p className="text-sm text-muted-foreground">₹{Math.ceil(totalAmount / m).toLocaleString()}/mo</p>
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">Your monthly payment: <strong>₹{monthlyAmount.toLocaleString()}</strong></p>
            <p className="text-xs text-green-700 mt-1">0% interest • No additional fees</p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={() => onSetup(months)}>Set Up Plan</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Patient Statement Component
interface PatientStatementProps {
  statement: Statement;
  hospitalName?: string;
  onPayNow: () => void;
  onSetupPlan: () => void;
  onAskQuestion: () => void;
}

export function PatientStatement({ statement, hospitalName = "Surya Hospitals", onPayNow, onSetupPlan, onAskQuestion }: PatientStatementProps) {
  const [paymentOption, setPaymentOption] = useState("full");
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [showPlanDialog, setShowPlanDialog] = useState(false);
  const { processPayment, setupPaymentPlan } = useBillingStore();

  const handlePayment = async (method: string, amount: number) => {
    await processPayment({ patientId: statement.patientId, statementId: statement.id, amount, method: method as Payment["method"] });
    setShowPaymentForm(false);
  };

  if (showPaymentForm) {
    return (
      <div className="max-w-lg mx-auto p-6">
        <PaymentForm amount={statement.totalDue} onSubmit={handlePayment} onCancel={() => setShowPaymentForm(false)} />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-2 text-primary mb-2">
          <Building2 className="h-6 w-6" /><span className="text-xl font-semibold">{hospitalName}</span>
        </div>
        <h1 className="text-lg text-muted-foreground">Your Statement</h1>
      </div>

      {/* Amount Due */}
      <Card className="border-2 border-primary">
        <CardContent className="p-6 text-center">
          <p className="text-sm text-muted-foreground">Amount Due</p>
          <p className="text-4xl font-bold text-primary mt-1">₹{statement.totalDue.toLocaleString()}</p>
          <p className="text-sm text-muted-foreground mt-2">Due Date: {format(new Date(statement.dueDate), "MMMM d, yyyy")}</p>
          <Button className="mt-4" size="lg" onClick={() => setShowPaymentForm(true)}><CreditCard className="h-5 w-5 mr-2" />Pay Now</Button>
        </CardContent>
      </Card>

      {/* Visit Details */}
      {statement.visits.map((visit, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex justify-between items-center">
              <CardTitle className="text-sm">VISIT DETAILS</CardTitle>
              <span className="text-sm text-muted-foreground">{format(new Date(visit.date), "MMMM d, yyyy")}</span>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-sm space-y-1">
              <p><span className="text-muted-foreground">Provider:</span> {visit.provider}</p>
              <p><span className="text-muted-foreground">Location:</span> {visit.location}</p>
              <p><span className="text-muted-foreground">Visit Type:</span> {visit.visitType}</p>
            </div>
            <Separator />
            <div className="space-y-2">
              <p className="text-sm font-medium">Services Provided:</p>
              {visit.services.map((svc, j) => (
                <div key={j} className="flex justify-between text-sm"><span>{svc.description}</span><span>₹{svc.amount.toLocaleString()}</span></div>
              ))}
              <Separator />
              <div className="flex justify-between text-sm font-medium"><span>Total Charges</span><span>₹{visit.totalCharges.toLocaleString()}</span></div>
              <div className="flex justify-between text-sm text-green-600"><span>Insurance Paid</span><span>-₹{visit.insurancePaid.toLocaleString()}</span></div>
              {visit.copayCollected > 0 && <div className="flex justify-between text-sm"><span>Copay (collected at visit)</span><span>-₹{visit.copayCollected.toLocaleString()}</span></div>}
              <Separator />
              <div className="flex justify-between font-bold"><span>AMOUNT DUE</span><span>₹{statement.totalDue.toLocaleString()}</span></div>
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Payment Options */}
      <Card>
        <CardContent className="p-4 space-y-3">
          <p className="font-medium">Payment Options:</p>
          <RadioGroup value={paymentOption} onValueChange={setPaymentOption}>
            <div className="flex items-center space-x-2"><RadioGroupItem value="full" id="full" /><Label htmlFor="full">Pay in full now (₹{statement.totalDue.toLocaleString()})</Label></div>
            {statement.paymentPlanAvailable && (
              <div className="flex items-center space-x-2"><RadioGroupItem value="plan" id="plan" /><Label htmlFor="plan">Set up payment plan (₹{Math.ceil(statement.totalDue / 3).toLocaleString()}/month for 3 months)</Label></div>
            )}
            <div className="flex items-center space-x-2"><RadioGroupItem value="partial" id="partial" /><Label htmlFor="partial">Pay partial amount</Label></div>
          </RadioGroup>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="outline" onClick={onAskQuestion}><MessageSquare className="h-4 w-4 mr-2" />Have Questions?</Button>
        <Button variant="outline"><Download className="h-4 w-4 mr-2" />Download PDF</Button>
        <Button className="flex-1" onClick={() => paymentOption === "plan" ? setShowPlanDialog(true) : setShowPaymentForm(true)}>
          <CreditCard className="h-4 w-4 mr-2" />{paymentOption === "plan" ? "Set Up Plan" : "Pay Now"} →
        </Button>
      </div>

      <PaymentPlanDialog open={showPlanDialog} onOpenChange={setShowPlanDialog} totalAmount={statement.totalDue} onSetup={(m) => { setupPaymentPlan(statement.id, m); setShowPlanDialog(false); }} />
    </div>
  );
}

// Statement Skeleton
export function StatementSkeleton() {
  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6 animate-pulse">
      <div className="text-center space-y-2"><div className="h-6 w-40 bg-muted rounded mx-auto" /><div className="h-4 w-24 bg-muted rounded mx-auto" /></div>
      <div className="border rounded-lg p-6"><div className="h-12 w-32 bg-muted rounded mx-auto" /></div>
      <div className="border rounded-lg p-6 space-y-4">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-4 bg-muted rounded" />)}</div>
    </div>
  );
}

export default PatientStatement;
