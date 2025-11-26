"use client";

// Claims Management Dashboard
// EPIC-UX-009: Billing & Revenue Portal - Journey 9.2

import React, { useEffect, useState } from "react";
import { format } from "date-fns";
import {
  FileText, Search, Filter, ChevronRight, Clock, Check, X, AlertTriangle,
  MoreVertical, Download, RefreshCw, Eye, Edit, Send,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useBillingStore, type Claim, type ClaimStatus } from "@/lib/store/billing-store";

// Claims Summary Cards
export function ClaimsSummaryCards() {
  const { claimsSummary } = useBillingStore();

  const cards = [
    { label: "Pending", count: claimsSummary.pending.count, amount: claimsSummary.pending.amount, color: "bg-amber-100 text-amber-700" },
    { label: "Submitted", count: claimsSummary.submitted.count, amount: claimsSummary.submitted.amount, color: "bg-blue-100 text-blue-700" },
    { label: "Denied", count: claimsSummary.denied.count, amount: claimsSummary.denied.amount, color: "bg-red-100 text-red-700" },
    { label: "Paid", count: claimsSummary.paid.count, amount: claimsSummary.paid.amount, color: "bg-green-100 text-green-700" },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map((card) => (
        <Card key={card.label}>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-muted-foreground">{card.label}</p>
            <p className="text-2xl font-bold">{card.count}</p>
            <Badge variant="secondary" className={cn("mt-1", card.color)}>
              ₹{(card.amount / 100000).toFixed(1)}L
            </Badge>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Claims Table
interface ClaimsTableProps {
  claims: Claim[];
  selectedClaims: string[];
  onSelectClaim: (claimId: string, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
  onViewClaim: (claimId: string) => void;
}

export function ClaimsTable({ claims, selectedClaims, onSelectClaim, onSelectAll, onViewClaim }: ClaimsTableProps) {
  const getStatusBadge = (status: ClaimStatus) => {
    const config = {
      draft: { icon: <Edit className="h-3 w-3" />, label: "Draft", className: "bg-gray-100 text-gray-700" },
      pending: { icon: <Clock className="h-3 w-3" />, label: "Pending", className: "bg-amber-100 text-amber-700" },
      submitted: { icon: <Send className="h-3 w-3" />, label: "Submitted", className: "bg-blue-100 text-blue-700" },
      accepted: { icon: <Check className="h-3 w-3" />, label: "Accepted", className: "bg-green-100 text-green-700" },
      denied: { icon: <X className="h-3 w-3" />, label: "Denied", className: "bg-red-100 text-red-700" },
      paid: { icon: <Check className="h-3 w-3" />, label: "Paid", className: "bg-green-100 text-green-700" },
      appealed: { icon: <AlertTriangle className="h-3 w-3" />, label: "Appealed", className: "bg-purple-100 text-purple-700" },
    };
    const c = config[status];
    return <Badge variant="secondary" className={cn("text-xs flex items-center gap-1", c.className)}>{c.icon}{c.label}</Badge>;
  };

  return (
    <div className="border rounded-lg">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr className="text-xs text-muted-foreground">
              <th className="p-3 text-left"><Checkbox checked={selectedClaims.length === claims.length} onCheckedChange={(c) => onSelectAll(!!c)} /></th>
              <th className="p-3 text-left">Claim #</th>
              <th className="p-3 text-left">Patient</th>
              <th className="p-3 text-left">DOS</th>
              <th className="p-3 text-right">Amount</th>
              <th className="p-3 text-left">Status</th>
              <th className="p-3"></th>
            </tr>
          </thead>
          <tbody>
            {claims.map((claim) => (
              <tr key={claim.id} className="border-t hover:bg-muted/30 cursor-pointer" onClick={() => onViewClaim(claim.id)}>
                <td className="p-3" onClick={(e) => e.stopPropagation()}>
                  <Checkbox checked={selectedClaims.includes(claim.id)} onCheckedChange={(c) => onSelectClaim(claim.id, !!c)} />
                </td>
                <td className="p-3">
                  <p className="font-medium text-sm">{claim.claimNumber}</p>
                  <p className="text-xs text-muted-foreground">{claim.insurance.payerName}</p>
                </td>
                <td className="p-3 text-sm">{claim.patientName}</td>
                <td className="p-3 text-sm">{format(new Date(claim.dateOfService), "MMM d")}</td>
                <td className="p-3 text-sm text-right font-medium">₹{claim.totalCharged.toLocaleString()}</td>
                <td className="p-3">
                  {getStatusBadge(claim.status)}
                  {claim.denialCode && <p className="text-xs text-red-600 mt-1">{claim.denialCode}</p>}
                </td>
                <td className="p-3" onClick={(e) => e.stopPropagation()}>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" className="h-8 w-8"><MoreVertical className="h-4 w-4" /></Button></DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onViewClaim(claim.id)}><Eye className="h-4 w-4 mr-2" />View Details</DropdownMenuItem>
                      <DropdownMenuItem><Edit className="h-4 w-4 mr-2" />Edit Claim</DropdownMenuItem>
                      {claim.status === "denied" && <DropdownMenuItem className="text-amber-600"><AlertTriangle className="h-4 w-4 mr-2" />Work Denial</DropdownMenuItem>}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Claim Detail Panel
interface ClaimDetailPanelProps {
  claim: Claim;
  onClose: () => void;
  onEdit: () => void;
  onResubmit: () => void;
}

export function ClaimDetailPanel({ claim, onClose, onEdit, onResubmit }: ClaimDetailPanelProps) {
  return (
    <Card className="w-96">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">{claim.claimNumber}</CardTitle>
          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}><X className="h-4 w-4" /></Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><span className="text-muted-foreground">Patient:</span> {claim.patientName}</div>
          <div><span className="text-muted-foreground">DOS:</span> {format(new Date(claim.dateOfService), "MMM d, yyyy")}</div>
          <div><span className="text-muted-foreground">Payer:</span> {claim.insurance.payerName}</div>
          <div><span className="text-muted-foreground">Total:</span> ₹{claim.totalCharged.toLocaleString()}</div>
        </div>

        <div className="space-y-2">
          <h4 className="text-xs font-medium text-muted-foreground">LINE ITEMS</h4>
          {claim.lineItems.map((item) => (
            <div key={item.id} className="flex justify-between text-sm p-2 bg-muted/50 rounded">
              <div><p className="font-medium">{item.cptCode}</p><p className="text-xs text-muted-foreground">{item.description}</p></div>
              <span>₹{item.chargeAmount.toLocaleString()}</span>
            </div>
          ))}
        </div>

        {claim.denialReason && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-xs font-medium text-red-800">Denial: {claim.denialCode}</p>
            <p className="text-xs text-red-700 mt-1">{claim.denialReason}</p>
          </div>
        )}

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onEdit}><Edit className="h-4 w-4 mr-1" />Edit</Button>
          {claim.status === "denied" && <Button size="sm" onClick={onResubmit}><RefreshCw className="h-4 w-4 mr-1" />Resubmit</Button>}
        </div>
      </CardContent>
    </Card>
  );
}

// Main Claims Dashboard
export function ClaimsDashboard() {
  const [selectedClaims, setSelectedClaims] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  const { claims, isLoadingClaims, fetchClaims, selectedClaim, fetchClaimDetail } = useBillingStore();

  useEffect(() => { fetchClaims(); }, [fetchClaims]);

  const filteredClaims = claims.filter((c) => {
    if (search && !c.claimNumber.toLowerCase().includes(search.toLowerCase()) && !c.patientName.toLowerCase().includes(search.toLowerCase())) return false;
    if (statusFilter && c.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2"><FileText className="h-6 w-6" />Claims Management</h1>
        <Button><RefreshCw className="h-4 w-4 mr-2" />Refresh</Button>
      </div>

      <ClaimsSummaryCards />

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search claims..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40"><SelectValue placeholder="All Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="submitted">Submitted</SelectItem>
            <SelectItem value="denied">Denied</SelectItem>
            <SelectItem value="paid">Paid</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          {isLoadingClaims ? (
            <div className="text-center py-8"><p>Loading claims...</p></div>
          ) : (
            <ClaimsTable
              claims={filteredClaims}
              selectedClaims={selectedClaims}
              onSelectClaim={(id, sel) => setSelectedClaims(sel ? [...selectedClaims, id] : selectedClaims.filter((c) => c !== id))}
              onSelectAll={(sel) => setSelectedClaims(sel ? filteredClaims.map((c) => c.id) : [])}
              onViewClaim={fetchClaimDetail}
            />
          )}
        </div>
        {selectedClaim && (
          <ClaimDetailPanel claim={selectedClaim} onClose={() => {}} onEdit={() => {}} onResubmit={() => {}} />
        )}
      </div>
    </div>
  );
}

export default ClaimsDashboard;
