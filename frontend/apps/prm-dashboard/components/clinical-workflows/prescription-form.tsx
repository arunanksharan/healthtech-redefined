"use client";

import * as React from "react";
import {
  Search,
  AlertTriangle,
  Pill,
  Check,
  X,
  Mic,
  ChevronRight,
  Building,
  Send,
  FileText,
  Clock,
  Plus,
  Minus,
  ExternalLink,
  ShieldAlert,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  useClinicalWorkflowsStore,
  type Medication,
  type Pharmacy,
  type DrugInteraction,
  type Prescription,
} from "@/lib/store/clinical-workflows-store";

// ============================================================================
// Types
// ============================================================================

interface PrescriptionFormProps {
  patientId: string;
  patientName: string;
  patientAllergies?: { allergen: string; severity: string; reaction?: string }[];
  currentMedications?: { name: string; dose: string }[];
  onSubmit: (prescription: Partial<Prescription>) => void;
  onCancel: () => void;
  className?: string;
}

interface MedicationSearchResult extends Medication {
  isPreviouslyPrescribed?: boolean;
}

// ============================================================================
// Frequency Options
// ============================================================================

const FREQUENCY_OPTIONS = [
  { value: "QD", label: "Once daily", description: "Take 1 time per day" },
  { value: "BID", label: "Twice daily", description: "Take 2 times per day" },
  { value: "TID", label: "Three times daily", description: "Take 3 times per day" },
  { value: "QID", label: "Four times daily", description: "Take 4 times per day" },
  { value: "QHS", label: "At bedtime", description: "Take at bedtime" },
  { value: "Q4H", label: "Every 4 hours", description: "Take every 4 hours" },
  { value: "Q6H", label: "Every 6 hours", description: "Take every 6 hours" },
  { value: "Q8H", label: "Every 8 hours", description: "Take every 8 hours" },
  { value: "PRN", label: "As needed", description: "Take as needed" },
  { value: "CUSTOM", label: "Custom...", description: "Enter custom frequency" },
];

const ROUTE_OPTIONS = [
  { value: "oral", label: "By Mouth (PO)" },
  { value: "sublingual", label: "Under Tongue (SL)" },
  { value: "topical", label: "Topical" },
  { value: "inhaled", label: "Inhaled" },
  { value: "ophthalmic", label: "Eye Drops" },
  { value: "otic", label: "Ear Drops" },
  { value: "subcutaneous", label: "Subcutaneous (SC)" },
  { value: "intramuscular", label: "Intramuscular (IM)" },
];

// ============================================================================
// Drug Interaction Alert Component
// ============================================================================

interface DrugInteractionAlertProps {
  interactions: DrugInteraction[];
  onAcknowledge: () => void;
  onCancel: () => void;
  isOpen: boolean;
}

function DrugInteractionAlert({
  interactions,
  onAcknowledge,
  onCancel,
  isOpen,
}: DrugInteractionAlertProps) {
  const [acknowledged, setAcknowledged] = React.useState(false);

  const severityColors = {
    severe: { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-500", icon: "text-red-500" },
    moderate: { bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-500", icon: "text-amber-500" },
    mild: { bg: "bg-blue-500/10", border: "border-blue-500/30", text: "text-blue-500", icon: "text-blue-500" },
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-amber-500" />
            Clinical Decision Support Alert
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {interactions.map((interaction, index) => {
            const colors = severityColors[interaction.severity];
            return (
              <div
                key={index}
                className={cn(
                  "p-4 rounded-lg border",
                  colors.bg,
                  colors.border
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Badge className={cn("uppercase text-xs", colors.bg, colors.text)}>
                    {interaction.severity} Interaction
                  </Badge>
                </div>
                <p className="font-medium mb-2">
                  {interaction.drug1} + {interaction.drug2}
                </p>
                <p className="text-sm text-muted-foreground mb-3">
                  <span className="font-medium">Risk:</span> {interaction.description}
                </p>
                <p className="text-sm text-muted-foreground mb-3">
                  <span className="font-medium">Recommendation:</span> {interaction.recommendation}
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>Evidence: Clinical Studies (Level {interaction.evidenceLevel})</span>
                  {interaction.evidenceLink && (
                    <Button variant="link" size="sm" className="h-auto p-0 text-xs">
                      View Evidence <ExternalLink className="h-3 w-3 ml-1" />
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex items-center gap-2 pt-4">
          <Checkbox
            id="acknowledge"
            checked={acknowledged}
            onCheckedChange={(checked) => setAcknowledged(checked as boolean)}
          />
          <Label htmlFor="acknowledge" className="text-sm">
            I have reviewed this interaction and wish to proceed
          </Label>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Cancel Prescription
          </Button>
          <Button onClick={onAcknowledge} disabled={!acknowledged}>
            Proceed with Caution
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// E-Signature Dialog Component
// ============================================================================

interface ESignatureDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSign: (pin: string) => void;
  prescription: {
    patientName: string;
    medication: string;
    directions: string;
    quantity: number;
    refills: number;
    pharmacy?: string;
  };
  prescriberInfo: {
    name: string;
    license: string;
  };
  interactions?: DrugInteraction[];
}

function ESignatureDialog({
  isOpen,
  onClose,
  onSign,
  prescription,
  prescriberInfo,
  interactions,
}: ESignatureDialogProps) {
  const [pin, setPin] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const handleSign = async () => {
    if (pin.length !== 4) return;
    setIsSubmitting(true);
    await new Promise((resolve) => setTimeout(resolve, 500));
    onSign(pin);
    setIsSubmitting(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Sign & Send Prescription
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Prescription Summary */}
          <div className="p-4 bg-muted/50 rounded-lg border">
            <h4 className="font-medium mb-3">Prescription Summary</h4>
            <div className="space-y-2 text-sm">
              <p><span className="text-muted-foreground">Patient:</span> {prescription.patientName}</p>
              <Separator />
              <div className="flex items-start gap-2">
                <Pill className="h-4 w-4 text-primary mt-0.5" />
                <div>
                  <p className="font-medium">{prescription.medication}</p>
                  <p className="text-muted-foreground">{prescription.directions}</p>
                  <p className="text-muted-foreground">
                    Qty: {prescription.quantity} • Refills: {prescription.refills}
                  </p>
                </div>
              </div>
              <Separator />
              <div className="flex items-center gap-2">
                <Building className="h-4 w-4 text-muted-foreground" />
                <span>{prescription.pharmacy || "Patient will pick up"}</span>
              </div>

              {interactions && interactions.length > 0 && (
                <>
                  <Separator />
                  <div className="flex items-center gap-2 text-amber-500">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="text-xs">
                      Reviewed: {interactions[0].severity} interaction with {interactions[0].drug2}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* E-Signature */}
          <div className="p-4 bg-muted/30 rounded-lg border">
            <h4 className="font-medium mb-3">Electronic Signature</h4>
            <div className="space-y-3">
              <div>
                <Label htmlFor="pin">Enter PIN to sign:</Label>
                <Input
                  id="pin"
                  type="password"
                  maxLength={4}
                  value={pin}
                  onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))}
                  placeholder="••••"
                  className="w-24 text-center text-lg tracking-widest mt-1"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                By signing, I certify this prescription is medically necessary.
              </p>
              <div className="text-sm">
                <p className="font-medium">{prescriberInfo.name}</p>
                <p className="text-muted-foreground">License: {prescriberInfo.license}</p>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Go Back
          </Button>
          <Button onClick={handleSign} disabled={pin.length !== 4 || isSubmitting}>
            {isSubmitting ? (
              <>
                <Clock className="h-4 w-4 mr-2 animate-spin" />
                Signing...
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Sign & Send
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Main Prescription Form Component
// ============================================================================

export function PrescriptionForm({
  patientId,
  patientName,
  patientAllergies = [],
  currentMedications = [],
  onSubmit,
  onCancel,
  className,
}: PrescriptionFormProps) {
  // Store
  const {
    medications,
    pharmacies,
    searchMedications,
    checkDrugInteractions,
  } = useClinicalWorkflowsStore();

  // Form State
  const [step, setStep] = React.useState<"search" | "details" | "review">("search");
  const [searchQuery, setSearchQuery] = React.useState("");
  const [searchResults, setSearchResults] = React.useState<MedicationSearchResult[]>([]);
  const [selectedMedication, setSelectedMedication] = React.useState<Medication | null>(null);
  const [isSearching, setIsSearching] = React.useState(false);

  // Prescription Details
  const [dose, setDose] = React.useState("1");
  const [doseUnit, setDoseUnit] = React.useState("tablet");
  const [route, setRoute] = React.useState("oral");
  const [frequency, setFrequency] = React.useState("BID");
  const [customFrequency, setCustomFrequency] = React.useState("");
  const [duration, setDuration] = React.useState("30");
  const [durationUnit, setDurationUnit] = React.useState<"days" | "weeks" | "months">("days");
  const [quantity, setQuantity] = React.useState("60");
  const [refills, setRefills] = React.useState("3");
  const [dispenseAsWritten, setDispenseAsWritten] = React.useState(false);
  const [directions, setDirections] = React.useState("");
  const [selectedPharmacy, setSelectedPharmacy] = React.useState<Pharmacy | null>(
    pharmacies.find((p) => p.isPreferred) || null
  );
  const [deliveryMethod, setDeliveryMethod] = React.useState<"electronic" | "print">("electronic");

  // Interaction State
  const [interactions, setInteractions] = React.useState<DrugInteraction[]>([]);
  const [showInteractionAlert, setShowInteractionAlert] = React.useState(false);
  const [interactionsAcknowledged, setInteractionsAcknowledged] = React.useState(false);

  // Signature State
  const [showSignatureDialog, setShowSignatureDialog] = React.useState(false);

  // Search medications
  const handleSearch = React.useCallback(async (query: string) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    const results = await searchMedications(query);
    setSearchResults(results);
    setIsSearching(false);
  }, [searchMedications]);

  // Select medication
  const handleSelectMedication = async (medication: Medication) => {
    setSelectedMedication(medication);

    // Generate default directions
    const defaultDirections = `Take ${dose} ${medication.form} ${route === "oral" ? "by mouth" : route} ${FREQUENCY_OPTIONS.find((f) => f.value === frequency)?.description || ""}`;
    setDirections(defaultDirections);

    // Check interactions
    const currentMedIds = currentMedications.map((_, i) => `current-${i}`);
    const drugInteractions = await checkDrugInteractions([medication.id, ...currentMedIds], patientId);
    setInteractions(drugInteractions);

    if (drugInteractions.length > 0) {
      setShowInteractionAlert(true);
    }

    setStep("details");
  };

  // Handle interaction acknowledgment
  const handleInteractionAcknowledge = () => {
    setInteractionsAcknowledged(true);
    setShowInteractionAlert(false);
  };

  // Calculate quantity based on dose and duration
  React.useEffect(() => {
    if (dose && duration && frequency !== "PRN") {
      const doseNum = parseInt(dose);
      const durationNum = parseInt(duration);
      const freqMultiplier =
        frequency === "QD" ? 1 :
        frequency === "BID" ? 2 :
        frequency === "TID" ? 3 :
        frequency === "QID" ? 4 :
        frequency === "Q6H" ? 4 :
        frequency === "Q8H" ? 3 :
        frequency === "Q4H" ? 6 : 1;

      const daysMultiplier =
        durationUnit === "days" ? durationNum :
        durationUnit === "weeks" ? durationNum * 7 :
        durationNum * 30;

      setQuantity(String(doseNum * freqMultiplier * daysMultiplier));
    }
  }, [dose, duration, durationUnit, frequency]);

  // Update directions when details change
  React.useEffect(() => {
    if (selectedMedication) {
      const freqLabel = FREQUENCY_OPTIONS.find((f) => f.value === frequency)?.description || "";
      const routeLabel = ROUTE_OPTIONS.find((r) => r.value === route)?.label || route;
      setDirections(
        `Take ${dose} ${selectedMedication.form}(s) ${routeLabel.toLowerCase()} ${freqLabel}`
      );
    }
  }, [dose, route, frequency, selectedMedication]);

  // Handle form submission
  const handleSubmit = () => {
    if (!selectedMedication) return;

    if (interactions.length > 0 && !interactionsAcknowledged) {
      setShowInteractionAlert(true);
      return;
    }

    setShowSignatureDialog(true);
  };

  // Handle signature
  const handleSign = (pin: string) => {
    if (!selectedMedication) return;

    const prescription: Partial<Prescription> = {
      patientId,
      medication: selectedMedication,
      dose: parseInt(dose),
      doseUnit,
      route,
      frequency: frequency === "CUSTOM" ? customFrequency : frequency,
      frequencyCode: frequency,
      duration: parseInt(duration),
      durationUnit,
      quantity: parseInt(quantity),
      quantityUnit: selectedMedication.form + "s",
      refills: parseInt(refills),
      dispenseAsWritten,
      directions,
      pharmacy: selectedPharmacy || undefined,
      status: "signed",
      interactions,
      interactionsReviewed: interactionsAcknowledged,
      signedAt: new Date().toISOString(),
    };

    onSubmit(prescription);
    setShowSignatureDialog(false);
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header with Allergies */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">New Prescription</CardTitle>
              <CardDescription>Patient: {patientName}</CardDescription>
            </div>
            <Button variant="ghost" size="icon" onClick={onCancel}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        {patientAllergies.length > 0 && (
          <CardContent className="pt-0">
            <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
              <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm font-medium">ALLERGIES</span>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {patientAllergies.map((allergy, index) => (
                  <Badge key={index} variant="outline" className="bg-amber-500/10 border-amber-500/30 text-amber-600">
                    {allergy.allergen} ({allergy.severity})
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Step 1: Medication Search */}
      {step === "search" && (
        <Card>
          <CardContent className="pt-6">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search medication..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-10 pr-10"
              />
              <Button variant="ghost" size="icon" className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8">
                <Mic className="h-4 w-4" />
              </Button>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="mt-4 border rounded-lg divide-y">
                {searchResults.map((medication) => (
                  <div
                    key={medication.id}
                    className="p-3 hover:bg-accent/50 cursor-pointer transition-colors"
                    onClick={() => handleSelectMedication(medication)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <RadioGroup value="">
                          <RadioGroupItem value={medication.id} className="border-primary" />
                        </RadioGroup>
                        <div>
                          <p className="font-medium">
                            {medication.name} {medication.strength} {medication.form}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {medication.genericName} • {medication.price ? `₹${medication.price}/${medication.priceUnit}` : "Price varies"}
                          </p>
                        </div>
                      </div>
                      {medication.isPreviouslyPrescribed && (
                        <Badge variant="outline" className="text-xs">
                          Previously Rx'd
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Empty State */}
            {searchQuery.length >= 2 && searchResults.length === 0 && !isSearching && (
              <div className="mt-4 text-center py-8 text-muted-foreground">
                <Pill className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No medications found for "{searchQuery}"</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 2: Prescription Details */}
      {step === "details" && selectedMedication && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Pill className="h-5 w-5 text-primary" />
              {selectedMedication.name} {selectedMedication.strength} {selectedMedication.form}
            </CardTitle>
            <CardDescription>{selectedMedication.genericName}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Dosage */}
            <div className="space-y-4">
              <h4 className="font-medium">Dosage</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Dose</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Input
                      type="number"
                      min="1"
                      value={dose}
                      onChange={(e) => setDose(e.target.value)}
                      className="w-20"
                    />
                    <Select value={doseUnit} onValueChange={setDoseUnit}>
                      <SelectTrigger className="w-[100px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="tablet">Tablet</SelectItem>
                        <SelectItem value="capsule">Capsule</SelectItem>
                        <SelectItem value="ml">mL</SelectItem>
                        <SelectItem value="mg">mg</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <Label>Route</Label>
                  <Select value={route} onValueChange={setRoute}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ROUTE_OPTIONS.map((r) => (
                        <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Frequency</Label>
                  <Select value={frequency} onValueChange={setFrequency}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {FREQUENCY_OPTIONS.map((f) => (
                        <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {frequency === "CUSTOM" && (
                <div>
                  <Label>Custom Frequency</Label>
                  <Input
                    value={customFrequency}
                    onChange={(e) => setCustomFrequency(e.target.value)}
                    placeholder="e.g., Every other day"
                    className="mt-1"
                  />
                </div>
              )}

              <div className="flex gap-4">
                <div>
                  <Label>Duration</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Input
                      type="number"
                      min="1"
                      value={duration}
                      onChange={(e) => setDuration(e.target.value)}
                      className="w-20"
                    />
                    <Select value={durationUnit} onValueChange={(v) => setDurationUnit(v as any)}>
                      <SelectTrigger className="w-[100px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="days">days</SelectItem>
                        <SelectItem value="weeks">weeks</SelectItem>
                        <SelectItem value="months">months</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Quick Select */}
              <div className="flex flex-wrap gap-2">
                <span className="text-sm text-muted-foreground mr-2">Quick Select:</span>
                {["Once daily", "Twice daily", "Three times", "PRN"].map((q) => (
                  <Button
                    key={q}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const freq = q === "Once daily" ? "QD" : q === "Twice daily" ? "BID" : q === "Three times" ? "TID" : "PRN";
                      setFrequency(freq);
                    }}
                  >
                    {q}
                  </Button>
                ))}
              </div>
            </div>

            <Separator />

            {/* Directions */}
            <div className="space-y-2">
              <Label>Directions (SIG)</Label>
              <Textarea
                value={directions}
                onChange={(e) => setDirections(e.target.value)}
                rows={2}
              />
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Info className="h-3 w-3" />
                Suggested: "Take with food to reduce stomach upset"
              </p>
            </div>

            <Separator />

            {/* Quantity & Refills */}
            <div className="space-y-4">
              <h4 className="font-medium">Quantity & Refills</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Quantity</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Input
                      type="number"
                      min="1"
                      value={quantity}
                      onChange={(e) => setQuantity(e.target.value)}
                      className="w-24"
                    />
                    <span className="text-sm text-muted-foreground">{selectedMedication.form}s</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">({duration}-day supply)</p>
                </div>
                <div>
                  <Label>Refills</Label>
                  <Select value={refills} onValueChange={setRefills}>
                    <SelectTrigger className="mt-1 w-24">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[0, 1, 2, 3, 4, 5, 6, 11].map((r) => (
                        <SelectItem key={r} value={String(r)}>
                          {r} {r === 11 ? "(1 year)" : ""}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Checkbox
                  id="daw"
                  checked={dispenseAsWritten}
                  onCheckedChange={(checked) => setDispenseAsWritten(checked as boolean)}
                />
                <Label htmlFor="daw" className="text-sm">
                  Dispense as Written (no substitution)
                </Label>
              </div>
            </div>

            <Separator />

            {/* Pharmacy Selection */}
            <div className="space-y-4">
              <h4 className="font-medium">Pharmacy</h4>
              <RadioGroup
                value={deliveryMethod}
                onValueChange={(v) => setDeliveryMethod(v as any)}
              >
                <div className="space-y-3">
                  {pharmacies.slice(0, 3).map((pharmacy) => (
                    <div
                      key={pharmacy.id}
                      className={cn(
                        "flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors",
                        selectedPharmacy?.id === pharmacy.id && "border-primary bg-primary/5"
                      )}
                      onClick={() => {
                        setSelectedPharmacy(pharmacy);
                        setDeliveryMethod("electronic");
                      }}
                    >
                      <RadioGroupItem value="electronic" checked={selectedPharmacy?.id === pharmacy.id} />
                      <Building className="h-4 w-4 text-muted-foreground" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">
                          {pharmacy.name}
                          {pharmacy.isPreferred && (
                            <Badge variant="secondary" className="ml-2 text-xs">Preferred</Badge>
                          )}
                        </p>
                        <p className="text-xs text-muted-foreground">{pharmacy.address}</p>
                      </div>
                    </div>
                  ))}

                  <div
                    className={cn(
                      "flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors",
                      deliveryMethod === "print" && "border-primary bg-primary/5"
                    )}
                    onClick={() => {
                      setSelectedPharmacy(null);
                      setDeliveryMethod("print");
                    }}
                  >
                    <RadioGroupItem value="print" checked={deliveryMethod === "print"} />
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">Print prescription</p>
                      <p className="text-xs text-muted-foreground">Patient will pick up from any pharmacy</p>
                    </div>
                  </div>
                </div>
              </RadioGroup>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      {step === "details" && (
        <div className="flex items-center justify-between">
          <Button variant="outline" onClick={() => setStep("search")}>
            Back to Search
          </Button>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>
              <Check className="h-4 w-4 mr-2" />
              Check & Prescribe
            </Button>
          </div>
        </div>
      )}

      {/* Drug Interaction Alert */}
      <DrugInteractionAlert
        interactions={interactions}
        onAcknowledge={handleInteractionAcknowledge}
        onCancel={() => setShowInteractionAlert(false)}
        isOpen={showInteractionAlert}
      />

      {/* E-Signature Dialog */}
      <ESignatureDialog
        isOpen={showSignatureDialog}
        onClose={() => setShowSignatureDialog(false)}
        onSign={handleSign}
        prescription={{
          patientName,
          medication: selectedMedication ? `${selectedMedication.name} ${selectedMedication.strength}` : "",
          directions,
          quantity: parseInt(quantity),
          refills: parseInt(refills),
          pharmacy: selectedPharmacy?.name,
        }}
        prescriberInfo={{
          name: "Dr. Rohit Sharma, MD",
          license: "KA-12345",
        }}
        interactions={interactions.length > 0 && interactionsAcknowledged ? interactions : undefined}
      />
    </div>
  );
}

export default PrescriptionForm;
