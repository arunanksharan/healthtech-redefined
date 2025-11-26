"use client";

// Patient Billing & Payments
// EPIC-UX-011: Patient Self-Service Portal - Journey 11.5

import React, { useEffect, useState } from "react";
import { format } from "date-fns";
import {
  CreditCard, DollarSign, FileText, Calendar, Check, Clock, AlertCircle,
  ChevronRight, Download, Plus, Loader2, Building2, HelpCircle, Phone,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  usePatientPortalStore,
  type Bill,
  type PaymentMethod,
  type PaymentPlan,
} from "@/lib/store/patient-portal-store";

// Bill status badge
function BillStatusBadge({ status }: { status: Bill["status"] }) {
  const config = {
    pending: { label: "Due", className: "bg-amber-100 text-amber-700", icon: Clock },
    paid: { label: "Paid", className: "bg-green-100 text-green-700", icon: Check },
    overdue: { label: "Overdue", className: "bg-red-100 text-red-700", icon: AlertCircle },
    payment_plan: { label: "Payment Plan", className: "bg-blue-100 text-blue-700", icon: Calendar },
  };
  const c = config[status];
  return (
    <Badge variant="secondary" className={cn("flex items-center gap-1", c.className)}>
      <c.icon className="h-3 w-3" />
      {c.label}
    </Badge>
  );
}

// Account summary card
interface AccountSummaryProps {
  totalBalance: number;
  onPayNow: () => void;
}

function AccountSummary({ totalBalance, onPayNow }: AccountSummaryProps) {
  return (
    <Card className="border-2 border-primary">
      <CardContent className="p-6 text-center">
        <p className="text-sm text-muted-foreground">Total Balance Due</p>
        <p className="text-4xl font-bold text-primary mt-2">
          ₹{totalBalance.toLocaleString()}
        </p>
        <Button className="mt-4" size="lg" onClick={onPayNow} disabled={totalBalance <= 0}>
          <CreditCard className="h-5 w-5 mr-2" />Pay Now
        </Button>
      </CardContent>
    </Card>
  );
}

// Bill card
interface BillCardProps {
  bill: Bill;
  onView: () => void;
  onPay: () => void;
}

function BillCard({ bill, onView, onPay }: BillCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-medium">{format(new Date(bill.serviceDate), "MMM d, yyyy")}</span>
              <span className="text-muted-foreground">-</span>
              <span>{bill.description}</span>
            </div>
            <p className="text-sm text-muted-foreground">{bill.provider}</p>
            <div className="flex items-center gap-4 mt-2">
              <BillStatusBadge status={bill.status} />
              {bill.status === "pending" && (
                <span className="text-xs text-muted-foreground">
                  Due: {format(new Date(bill.dueDate), "MMM d")}
                </span>
              )}
            </div>
          </div>
          <div className="text-right">
            <p className="text-lg font-bold">
              {bill.balance > 0 ? `₹${bill.balance.toLocaleString()}` : "₹0"}
            </p>
            {bill.balance > 0 && bill.balance < bill.patientResponsibility && (
              <p className="text-xs text-green-600">
                ₹{(bill.patientResponsibility - bill.balance).toLocaleString()} paid
              </p>
            )}
          </div>
        </div>
        <div className="flex gap-2 mt-4">
          <Button variant="outline" size="sm" onClick={onView}>
            View Details
          </Button>
          {bill.balance > 0 && (
            <Button size="sm" onClick={onPay}>
              Pay This Bill
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Bill detail dialog
interface BillDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  bill: Bill | null;
  onPay: () => void;
}

function BillDetailDialog({ open, onOpenChange, bill, onPay }: BillDetailDialogProps) {
  if (!bill) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Statement Details</DialogTitle>
          <DialogDescription>
            Service Date: {format(new Date(bill.serviceDate), "MMMM d, yyyy")}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold">{bill.description}</p>
              <p className="text-sm text-muted-foreground">{bill.provider}</p>
            </div>
            <BillStatusBadge status={bill.status} />
          </div>

          <Separator />

          {/* Line items */}
          <div className="space-y-2">
            <p className="text-sm font-medium">Services</p>
            {bill.lineItems.map((item, i) => (
              <div key={i} className="flex justify-between text-sm py-2 border-b last:border-0">
                <span>{item.description}</span>
                <span>₹{item.amount.toLocaleString()}</span>
              </div>
            ))}
          </div>

          <Separator />

          {/* Summary */}
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Total Charges</span>
              <span>₹{bill.totalAmount.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-green-600">
              <span>Insurance Paid</span>
              <span>-₹{bill.insurancePaid.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span>Patient Responsibility</span>
              <span>₹{bill.patientResponsibility.toLocaleString()}</span>
            </div>
            {bill.amountPaid > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Amount Paid</span>
                <span>-₹{bill.amountPaid.toLocaleString()}</span>
              </div>
            )}
            <Separator />
            <div className="flex justify-between font-bold text-lg">
              <span>Balance Due</span>
              <span>₹{bill.balance.toLocaleString()}</span>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
          {bill.balance > 0 && <Button onClick={onPay}>Pay ₹{bill.balance.toLocaleString()}</Button>}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Payment dialog
interface PaymentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  bill: Bill | null;
  paymentMethods: PaymentMethod[];
  onPay: (paymentMethodId: string, amount: number) => Promise<void>;
  isProcessing: boolean;
}

function PaymentDialog({ open, onOpenChange, bill, paymentMethods, onPay, isProcessing }: PaymentDialogProps) {
  const [selectedMethod, setSelectedMethod] = useState(paymentMethods.find((m) => m.isDefault)?.id || "");
  const [amount, setAmount] = useState(bill?.balance.toString() || "");

  useEffect(() => {
    if (bill) setAmount(bill.balance.toString());
  }, [bill]);

  if (!bill) return null;

  const handlePay = async () => {
    await onPay(selectedMethod, parseFloat(amount));
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Make a Payment</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="text-center p-4 bg-primary/10 rounded-lg">
            <p className="text-sm text-muted-foreground">Amount to Pay</p>
            <div className="flex items-center justify-center gap-2 mt-1">
              <span className="text-2xl font-bold">₹</span>
              <Input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-32 text-2xl font-bold text-center border-0 bg-transparent"
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Balance: ₹{bill.balance.toLocaleString()}
            </p>
          </div>

          <div className="space-y-2">
            <Label>Payment Method</Label>
            <RadioGroup value={selectedMethod} onValueChange={setSelectedMethod}>
              {paymentMethods.map((method) => (
                <div
                  key={method.id}
                  className={cn(
                    "flex items-center space-x-3 p-3 rounded-lg border cursor-pointer",
                    selectedMethod === method.id && "border-primary bg-primary/5"
                  )}
                  onClick={() => setSelectedMethod(method.id)}
                >
                  <RadioGroupItem value={method.id} id={method.id} />
                  <Label htmlFor={method.id} className="flex-1 cursor-pointer flex items-center gap-3">
                    <CreditCard className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{method.brand} •••• {method.last4}</p>
                      {method.expiryMonth && method.expiryYear && (
                        <p className="text-xs text-muted-foreground">
                          Expires {method.expiryMonth}/{method.expiryYear}
                        </p>
                      )}
                    </div>
                    {method.isDefault && <Badge variant="secondary" className="ml-auto">Default</Badge>}
                  </Label>
                </div>
              ))}
            </RadioGroup>
            <Button variant="outline" className="w-full" size="sm">
              <Plus className="h-4 w-4 mr-2" />Add Payment Method
            </Button>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            onClick={handlePay}
            disabled={!selectedMethod || !amount || parseFloat(amount) <= 0 || isProcessing}
          >
            {isProcessing ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Processing...</>
            ) : (
              `Pay ₹${parseFloat(amount || "0").toLocaleString()}`
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Payment plan dialog
interface PaymentPlanDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  bill: Bill | null;
  onSetup: (months: number) => Promise<void>;
}

function PaymentPlanDialog({ open, onOpenChange, bill, onSetup }: PaymentPlanDialogProps) {
  const [months, setMonths] = useState(3);
  const [isSettingUp, setIsSettingUp] = useState(false);

  if (!bill) return null;

  const monthlyAmount = Math.ceil(bill.balance / months);

  const handleSetup = async () => {
    setIsSettingUp(true);
    await onSetup(months);
    setIsSettingUp(false);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Set Up Payment Plan</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <p className="text-sm text-muted-foreground">Total Balance</p>
            <p className="text-2xl font-bold">₹{bill.balance.toLocaleString()}</p>
          </div>

          <div className="space-y-2">
            <Label>Number of Payments</Label>
            <RadioGroup
              value={String(months)}
              onValueChange={(v) => setMonths(Number(v))}
              className="grid grid-cols-3 gap-2"
            >
              {[3, 6, 12].map((m) => (
                <div
                  key={m}
                  className={cn(
                    "p-4 border rounded-lg text-center cursor-pointer transition-colors",
                    months === m && "border-primary bg-primary/5"
                  )}
                  onClick={() => setMonths(m)}
                >
                  <RadioGroupItem value={String(m)} id={`m-${m}`} className="sr-only" />
                  <Label htmlFor={`m-${m}`} className="cursor-pointer">
                    <p className="font-medium">{m} months</p>
                    <p className="text-sm text-muted-foreground">
                      ₹{Math.ceil(bill.balance / m).toLocaleString()}/mo
                    </p>
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>

          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              Your monthly payment: <strong>₹{monthlyAmount.toLocaleString()}</strong>
            </p>
            <p className="text-xs text-green-700 mt-1">0% interest • No additional fees</p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSetup} disabled={isSettingUp}>
            {isSettingUp ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
            Set Up Plan
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Main Patient Billing Component
export function PatientBilling() {
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);
  const [showBillDetail, setShowBillDetail] = useState(false);
  const [showPayment, setShowPayment] = useState(false);
  const [showPaymentPlan, setShowPaymentPlan] = useState(false);

  const {
    bills,
    totalBalance,
    paymentMethods,
    paymentPlan,
    isLoadingBills,
    isProcessingPayment,
    fetchBills,
    makePayment,
    setupPaymentPlan,
  } = usePatientPortalStore();

  useEffect(() => { fetchBills(); }, [fetchBills]);

  const handleViewBill = (bill: Bill) => {
    setSelectedBill(bill);
    setShowBillDetail(true);
  };

  const handlePayBill = (bill: Bill) => {
    setSelectedBill(bill);
    setShowPayment(true);
  };

  const handleMakePayment = async (paymentMethodId: string, amount: number) => {
    if (selectedBill) {
      await makePayment(selectedBill.id, amount, paymentMethodId);
    }
  };

  const handleSetupPlan = async (months: number) => {
    if (selectedBill) {
      await setupPaymentPlan(selectedBill.id, months);
    }
  };

  const pendingBills = bills.filter((b) => b.status === "pending" || b.status === "overdue");
  const paidBills = bills.filter((b) => b.status === "paid");

  if (isLoadingBills) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <CreditCard className="h-6 w-6" />My Bills
        </h1>
      </div>

      {/* Account Summary */}
      <AccountSummary
        totalBalance={totalBalance}
        onPayNow={() => {
          const firstPending = pendingBills[0];
          if (firstPending) handlePayBill(firstPending);
        }}
      />

      {/* Payment Plan Info */}
      {paymentPlan && paymentPlan.status === "active" && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-blue-800">Active Payment Plan</p>
                <p className="text-sm text-blue-700">
                  ₹{paymentPlan.monthlyPayment.toLocaleString()}/month • {paymentPlan.remainingPayments} payments remaining
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Next payment: {format(new Date(paymentPlan.nextPaymentDate), "MMM d, yyyy")}
                </p>
              </div>
              <Button variant="outline">Manage Plan</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Statements */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Statements</h2>

        {pendingBills.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm font-medium text-muted-foreground">Outstanding ({pendingBills.length})</p>
            {pendingBills.map((bill) => (
              <BillCard
                key={bill.id}
                bill={bill}
                onView={() => handleViewBill(bill)}
                onPay={() => handlePayBill(bill)}
              />
            ))}
          </div>
        )}

        {paidBills.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm font-medium text-muted-foreground">Paid ({paidBills.length})</p>
            {paidBills.map((bill) => (
              <BillCard
                key={bill.id}
                bill={bill}
                onView={() => handleViewBill(bill)}
                onPay={() => {}}
              />
            ))}
          </div>
        )}
      </div>

      {/* Payment Methods */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">PAYMENT METHODS</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {paymentMethods.map((method) => (
            <div key={method.id} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <CreditCard className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="font-medium">{method.brand} •••• {method.last4}</p>
                  {method.expiryMonth && method.expiryYear && (
                    <p className="text-xs text-muted-foreground">
                      Expires {method.expiryMonth}/{method.expiryYear}
                    </p>
                  )}
                </div>
              </div>
              {method.isDefault && <Badge variant="secondary">Default</Badge>}
            </div>
          ))}
          <Button variant="outline" className="w-full">
            <Plus className="h-4 w-4 mr-2" />Add Payment Method
          </Button>
        </CardContent>
      </Card>

      {/* Help Section */}
      <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
        <div className="flex items-center gap-2">
          <HelpCircle className="h-5 w-5 text-muted-foreground" />
          <span className="text-sm">Need help?</span>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const firstPending = pendingBills[0];
              if (firstPending) {
                setSelectedBill(firstPending);
                setShowPaymentPlan(true);
              }
            }}
          >
            Set Up Payment Plan
          </Button>
          <Button variant="outline" size="sm">
            <Phone className="h-4 w-4 mr-2" />Contact Billing
          </Button>
        </div>
      </div>

      {/* Dialogs */}
      <BillDetailDialog
        open={showBillDetail}
        onOpenChange={setShowBillDetail}
        bill={selectedBill}
        onPay={() => {
          setShowBillDetail(false);
          setShowPayment(true);
        }}
      />

      <PaymentDialog
        open={showPayment}
        onOpenChange={setShowPayment}
        bill={selectedBill}
        paymentMethods={paymentMethods}
        onPay={handleMakePayment}
        isProcessing={isProcessingPayment}
      />

      <PaymentPlanDialog
        open={showPaymentPlan}
        onOpenChange={setShowPaymentPlan}
        bill={selectedBill}
        onSetup={handleSetupPlan}
      />
    </div>
  );
}

export default PatientBilling;
