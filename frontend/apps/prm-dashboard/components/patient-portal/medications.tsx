"use client";

// Medication Management & Refill Requests
// EPIC-UX-011: Patient Self-Service Portal - Journey 11.4

import React, { useEffect, useState } from "react";
import { format, isPast, addDays } from "date-fns";
import {
  Pill, RefreshCw, AlertCircle, Check, Clock, MessageSquare, ChevronRight,
  Calendar, Building2, User, Loader2, Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  usePatientPortalStore,
  type Medication,
  type RefillRequest,
} from "@/lib/store/patient-portal-store";

// Refill status badge
function RefillStatusBadge({ status }: { status: RefillRequest["status"] }) {
  const config = {
    pending: { label: "Pending", className: "bg-amber-100 text-amber-700", icon: Clock },
    approved: { label: "Approved", className: "bg-blue-100 text-blue-700", icon: Check },
    denied: { label: "Denied", className: "bg-red-100 text-red-700", icon: AlertCircle },
    ready_for_pickup: { label: "Ready for Pickup", className: "bg-green-100 text-green-700", icon: Check },
  };
  const c = config[status];
  return (
    <Badge variant="secondary" className={cn("flex items-center gap-1", c.className)}>
      <c.icon className="h-3 w-3" />
      {c.label}
    </Badge>
  );
}

// Medication card
interface MedicationCardProps {
  medication: Medication;
  onRequestRefill: () => void;
  onRequestNewPrescription: () => void;
  isRequestingRefill: boolean;
}

function MedicationCard({ medication, onRequestRefill, onRequestNewPrescription, isRequestingRefill }: MedicationCardProps) {
  const canRefill = medication.refillsRemaining > 0;
  const nextRefillAvailable = new Date(medication.nextRefillDate);
  const isRefillAvailable = isPast(nextRefillAvailable) || isPast(addDays(nextRefillAvailable, -7));
  const refillProgress = ((medication.totalRefills - medication.refillsRemaining) / medication.totalRefills) * 100;

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
            <Pill className="h-6 w-6 text-primary" />
          </div>
          <div className="flex-1 space-y-3">
            <div>
              <h3 className="font-semibold">{medication.name}</h3>
              <p className="text-sm text-muted-foreground">{medication.instructions}</p>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Prescriber:</span>
                <span>{medication.prescriber}</span>
              </div>
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Pharmacy:</span>
                <span>{medication.pharmacy.split(",")[0]}</span>
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Refills Remaining:</span>
                <span className="font-medium">{medication.refillsRemaining} of {medication.totalRefills}</span>
              </div>
              <Progress value={100 - refillProgress} className="h-2" />
            </div>

            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>Last Filled: {format(new Date(medication.lastFilledDate), "MMM d, yyyy")}</span>
              </div>
              <div className="flex items-center gap-2">
                {isRefillAvailable ? (
                  <Badge variant="outline" className="text-green-600 border-green-600">
                    Refill Available
                  </Badge>
                ) : (
                  <span className="text-muted-foreground text-xs">
                    Next refill: {format(nextRefillAvailable, "MMM d")}
                  </span>
                )}
              </div>
            </div>

            {!canRefill && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  No refills remaining. Contact your doctor for a new prescription.
                </AlertDescription>
              </Alert>
            )}

            <div className="flex gap-2 pt-2">
              {canRefill ? (
                <Button
                  onClick={onRequestRefill}
                  disabled={!isRefillAvailable || isRequestingRefill}
                  className="flex-1"
                >
                  {isRequestingRefill ? (
                    <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Requesting...</>
                  ) : (
                    <><RefreshCw className="h-4 w-4 mr-2" />Request Refill</>
                  )}
                </Button>
              ) : (
                <Button
                  variant="outline"
                  onClick={onRequestNewPrescription}
                  className="flex-1"
                >
                  <MessageSquare className="h-4 w-4 mr-2" />Request New Prescription
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Refill request card
function RefillRequestCard({ request }: { request: RefillRequest }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">{request.medicationName}</p>
            <p className="text-xs text-muted-foreground">
              Requested: {format(new Date(request.requestedAt), "MMM d, yyyy h:mm a")}
            </p>
            {request.processedAt && (
              <p className="text-xs text-muted-foreground">
                Processed: {format(new Date(request.processedAt), "MMM d, yyyy")}
              </p>
            )}
          </div>
          <RefillStatusBadge status={request.status} />
        </div>
        {request.notes && (
          <p className="text-sm text-muted-foreground mt-2 p-2 bg-muted/50 rounded">
            {request.notes}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// Refill confirmation dialog
interface RefillDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  medication: Medication | null;
  onConfirm: () => void;
  isRequesting: boolean;
}

function RefillDialog({ open, onOpenChange, medication, onConfirm, isRequesting }: RefillDialogProps) {
  if (!medication) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Request Refill</DialogTitle>
          <DialogDescription>
            Confirm your refill request for the following medication.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="p-4 bg-muted/50 rounded-lg space-y-2">
            <p className="font-semibold">{medication.name}</p>
            <p className="text-sm text-muted-foreground">{medication.dosage} - {medication.frequency}</p>
            <p className="text-sm">{medication.instructions}</p>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Pharmacy</p>
              <p className="font-medium">{medication.pharmacy}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Refills Remaining</p>
              <p className="font-medium">{medication.refillsRemaining - 1} after this refill</p>
            </div>
          </div>
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Your refill will be sent to {medication.pharmacy}. You'll receive a notification when it's ready for pickup.
            </AlertDescription>
          </Alert>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={onConfirm} disabled={isRequesting}>
            {isRequesting ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Requesting...</>
            ) : (
              "Confirm Refill Request"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Main Medications Component
export function Medications() {
  const [activeTab, setActiveTab] = useState("active");
  const [selectedMedication, setSelectedMedication] = useState<Medication | null>(null);
  const [showRefillDialog, setShowRefillDialog] = useState(false);

  const {
    medications,
    refillRequests,
    isLoadingMedications,
    isRequestingRefill,
    fetchMedications,
    requestRefill,
  } = usePatientPortalStore();

  useEffect(() => { fetchMedications(); }, [fetchMedications]);

  const activeMedications = medications.filter((m) => m.status === "active");
  const pastMedications = medications.filter((m) => m.status !== "active");

  const handleRequestRefill = (medication: Medication) => {
    setSelectedMedication(medication);
    setShowRefillDialog(true);
  };

  const handleConfirmRefill = async () => {
    if (selectedMedication) {
      await requestRefill(selectedMedication.id);
      setShowRefillDialog(false);
      setSelectedMedication(null);
    }
  };

  if (isLoadingMedications) {
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
          <Pill className="h-6 w-6" />My Medications
        </h1>
        <Badge variant="secondary">{activeMedications.length} Active</Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="active">Active ({activeMedications.length})</TabsTrigger>
          <TabsTrigger value="past">Past ({pastMedications.length})</TabsTrigger>
          <TabsTrigger value="requests">
            Refill Requests
            {refillRequests.filter((r) => r.status === "pending").length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {refillRequests.filter((r) => r.status === "pending").length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="mt-6 space-y-4">
          {activeMedications.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No active medications
              </CardContent>
            </Card>
          ) : (
            activeMedications.map((med) => (
              <MedicationCard
                key={med.id}
                medication={med}
                onRequestRefill={() => handleRequestRefill(med)}
                onRequestNewPrescription={() => {}}
                isRequestingRefill={isRequestingRefill && selectedMedication?.id === med.id}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="past" className="mt-6 space-y-4">
          {pastMedications.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No past medications
              </CardContent>
            </Card>
          ) : (
            pastMedications.map((med) => (
              <Card key={med.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{med.name}</p>
                      <p className="text-sm text-muted-foreground">{med.instructions}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {format(new Date(med.startDate), "MMM yyyy")} - {med.endDate ? format(new Date(med.endDate), "MMM yyyy") : "Present"}
                      </p>
                    </div>
                    <Badge variant="outline" className="capitalize">{med.status}</Badge>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="requests" className="mt-6 space-y-4">
          {refillRequests.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No refill requests
              </CardContent>
            </Card>
          ) : (
            refillRequests.map((request) => (
              <RefillRequestCard key={request.id} request={request} />
            ))
          )}
        </TabsContent>
      </Tabs>

      <RefillDialog
        open={showRefillDialog}
        onOpenChange={setShowRefillDialog}
        medication={selectedMedication}
        onConfirm={handleConfirmRefill}
        isRequesting={isRequestingRefill}
      />
    </div>
  );
}

export default Medications;
