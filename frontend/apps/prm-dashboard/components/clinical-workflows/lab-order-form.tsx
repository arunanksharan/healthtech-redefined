"use client";

// Lab Order Form Component
// EPIC-UX-007: Clinical Workflows Interface - Journey 7.2 Lab Order Management

import React, { useState, useMemo, useCallback } from "react";
import { format } from "date-fns";
import {
  Search,
  Plus,
  X,
  Beaker,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Building2,
  MapPin,
  FileText,
  ChevronRight,
  ChevronDown,
  Coffee,
  DollarSign,
  Stethoscope,
  Calendar,
  Printer,
  Send,
  Loader2,
  Info,
  Package,
  Trash2,
  Star,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  useClinicalWorkflowsStore,
  type LabTest,
  type LabOrder,
  type LabFacility,
  type DiagnosisCode,
} from "@/lib/store/clinical-workflows-store";

// ============================================================================
// Types
// ============================================================================

interface LabOrderFormProps {
  patientId: string;
  patientName: string;
  patientDOB?: string;
  patientInsurance?: {
    provider: string;
    memberId: string;
    groupNumber?: string;
  };
  onSubmit: (order: Partial<LabOrder>) => void;
  onCancel: () => void;
}

interface SelectedTest extends LabTest {
  quantity?: number;
  specialInstructions?: string;
}

interface LabPanel {
  id: string;
  name: string;
  description: string;
  tests: string[]; // Test IDs
  commonUse: string;
  totalPrice: number;
}

// ============================================================================
// Mock Data - Lab Panels
// ============================================================================

const LAB_PANELS: LabPanel[] = [
  {
    id: "panel-cmp",
    name: "Comprehensive Metabolic Panel (CMP)",
    description: "14 tests for kidney, liver, and metabolic function",
    tests: ["lab-glucose", "lab-bun", "lab-creatinine", "lab-sodium", "lab-potassium"],
    commonUse: "Annual physical, diabetes monitoring, kidney function",
    totalPrice: 45,
  },
  {
    id: "panel-bmp",
    name: "Basic Metabolic Panel (BMP)",
    description: "8 tests for kidney function and electrolytes",
    tests: ["lab-glucose", "lab-bun", "lab-creatinine", "lab-sodium", "lab-potassium"],
    commonUse: "Routine health check, medication monitoring",
    totalPrice: 35,
  },
  {
    id: "panel-lipid",
    name: "Lipid Panel",
    description: "Complete cholesterol and triglyceride analysis",
    tests: ["lab-lipid"],
    commonUse: "Cardiovascular risk assessment, statin monitoring",
    totalPrice: 30,
  },
  {
    id: "panel-cbc",
    name: "Complete Blood Count with Differential",
    description: "White cells, red cells, hemoglobin, hematocrit, platelets",
    tests: ["lab-cbc"],
    commonUse: "Infection, anemia, blood disorders",
    totalPrice: 25,
  },
  {
    id: "panel-thyroid",
    name: "Thyroid Panel",
    description: "TSH, T3, T4 for thyroid function",
    tests: ["lab-tsh"],
    commonUse: "Thyroid disorders, medication adjustment",
    totalPrice: 55,
  },
  {
    id: "panel-liver",
    name: "Hepatic Function Panel",
    description: "Complete liver enzyme and function tests",
    tests: ["lab-alt", "lab-ast"],
    commonUse: "Liver disease, medication monitoring",
    totalPrice: 40,
  },
  {
    id: "panel-diabetes",
    name: "Diabetes Management Panel",
    description: "HbA1c, glucose, kidney function markers",
    tests: ["lab-hba1c", "lab-glucose", "lab-creatinine"],
    commonUse: "Diabetes monitoring, quarterly check",
    totalPrice: 50,
  },
];

// Mock Diagnosis Codes
const COMMON_DIAGNOSIS_CODES: DiagnosisCode[] = [
  { code: "Z00.00", description: "Encounter for general adult medical examination", category: "Preventive" },
  { code: "E11.9", description: "Type 2 diabetes mellitus without complications", category: "Endocrine" },
  { code: "E78.5", description: "Hyperlipidemia, unspecified", category: "Metabolic" },
  { code: "I10", description: "Essential (primary) hypertension", category: "Cardiovascular" },
  { code: "E03.9", description: "Hypothyroidism, unspecified", category: "Endocrine" },
  { code: "D64.9", description: "Anemia, unspecified", category: "Blood" },
  { code: "N18.3", description: "Chronic kidney disease, stage 3", category: "Renal" },
  { code: "K76.0", description: "Fatty (change of) liver, not elsewhere classified", category: "Hepatic" },
  { code: "R53.83", description: "Other fatigue", category: "Symptoms" },
  { code: "R63.4", description: "Abnormal weight loss", category: "Symptoms" },
];

// Mock Lab Facilities
const LAB_FACILITIES: LabFacility[] = [
  {
    id: "fac-quest-main",
    name: "Quest Diagnostics - Main Street",
    address: "123 Main Street, Suite 100",
    city: "San Francisco",
    state: "CA",
    zipCode: "94102",
    phone: "(415) 555-0101",
    fax: "(415) 555-0102",
    isInNetwork: true,
    acceptedInsurance: ["Blue Cross", "Aetna", "United", "Medicare"],
    capabilities: ["Blood Draw", "Urine Collection", "Drug Screen"],
    operatingHours: "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
    electronicOrdering: true,
    averageWaitTime: "15 min",
  },
  {
    id: "fac-labcorp-downtown",
    name: "LabCorp - Downtown Center",
    address: "456 Market Street, Floor 2",
    city: "San Francisco",
    state: "CA",
    zipCode: "94103",
    phone: "(415) 555-0201",
    fax: "(415) 555-0202",
    isInNetwork: true,
    acceptedInsurance: ["Blue Cross", "Cigna", "United", "Medicaid"],
    capabilities: ["Blood Draw", "Urine Collection", "Genetic Testing"],
    operatingHours: "Mon-Fri 6AM-8PM, Sat-Sun 8AM-4PM",
    electronicOrdering: true,
    averageWaitTime: "20 min",
  },
  {
    id: "fac-inhouse",
    name: "In-Office Collection",
    address: "Your clinic location",
    city: "San Francisco",
    state: "CA",
    zipCode: "94102",
    phone: "(415) 555-0001",
    fax: "(415) 555-0002",
    isInNetwork: true,
    acceptedInsurance: ["All insurances"],
    capabilities: ["Blood Draw", "Rapid Tests", "POC Testing"],
    operatingHours: "During clinic hours",
    electronicOrdering: false,
    averageWaitTime: "5 min",
  },
];

// ============================================================================
// Sub-Components
// ============================================================================

// Test Search Component
interface TestSearchProps {
  onSelectTest: (test: LabTest) => void;
  selectedTestIds: string[];
}

function TestSearch({ onSelectTest, selectedTestIds }: TestSearchProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { labTests, searchLabTests, isLoadingLabTests } = useClinicalWorkflowsStore();

  const handleSearch = useCallback((value: string) => {
    setSearch(value);
    if (value.length >= 2) {
      searchLabTests(value);
    }
  }, [searchLabTests]);

  const filteredTests = labTests.filter(
    (test) => !selectedTestIds.includes(test.id)
  );

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-start text-muted-foreground"
        >
          <Search className="mr-2 h-4 w-4" />
          Search lab tests by name or code...
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[500px] p-0" align="start">
        <Command>
          <CommandInput
            placeholder="Search tests (e.g., CBC, glucose, lipid)..."
            value={search}
            onValueChange={handleSearch}
          />
          <CommandList>
            <CommandEmpty>
              {isLoadingLabTests ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Searching...
                </div>
              ) : (
                "No tests found."
              )}
            </CommandEmpty>
            <CommandGroup heading="Available Tests">
              {filteredTests.map((test) => (
                <CommandItem
                  key={test.id}
                  onSelect={() => {
                    onSelectTest(test);
                    setOpen(false);
                    setSearch("");
                  }}
                  className="flex items-center justify-between py-3"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Beaker className="h-4 w-4 text-primary" />
                      <span className="font-medium">{test.name}</span>
                      {test.requiresFasting && (
                        <Badge variant="secondary" className="text-xs">
                          <Coffee className="h-3 w-3 mr-1" />
                          Fasting
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                      <span>LOINC: {test.loinc || test.code}</span>
                      <span>CPT: {test.cptCode}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {test.turnaroundTime}
                      </span>
                    </div>
                  </div>
                  <span className="text-sm font-medium text-green-600">
                    ${(test.price ?? 0).toFixed(2)}
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

// Panel Selection Card
interface PanelCardProps {
  panel: LabPanel;
  isSelected: boolean;
  onToggle: () => void;
}

function PanelCard({ panel, isSelected, onToggle }: PanelCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all",
        isSelected && "ring-2 ring-primary bg-primary/5"
      )}
    >
      <CardHeader className="py-3 px-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <Checkbox
              checked={isSelected}
              onCheckedChange={onToggle}
              className="mt-1"
            />
            <div className="flex-1">
              <CardTitle className="text-sm font-medium">{panel.name}</CardTitle>
              <CardDescription className="text-xs mt-1">
                {panel.description}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              <DollarSign className="h-3 w-3" />
              {panel.totalPrice}
            </Badge>
            <Collapsible open={expanded} onOpenChange={setExpanded}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6">
                  {expanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </Collapsible>
          </div>
        </div>
        <Collapsible open={expanded} onOpenChange={setExpanded}>
          <CollapsibleContent>
            <div className="mt-3 pt-3 border-t text-xs text-muted-foreground">
              <p className="flex items-center gap-1 mb-2">
                <Stethoscope className="h-3 w-3" />
                <strong>Common Use:</strong> {panel.commonUse}
              </p>
              <p className="flex items-center gap-1">
                <Package className="h-3 w-3" />
                <strong>Includes:</strong> {panel.tests.length} tests
              </p>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardHeader>
    </Card>
  );
}

// Selected Test Item
interface SelectedTestItemProps {
  test: SelectedTest;
  onRemove: () => void;
  onUpdateInstructions: (instructions: string) => void;
}

function SelectedTestItem({ test, onRemove, onUpdateInstructions }: SelectedTestItemProps) {
  const [showInstructions, setShowInstructions] = useState(false);

  return (
    <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
      <Beaker className="h-5 w-5 text-primary mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{test.name}</span>
          {test.requiresFasting && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Badge variant="outline" className="text-xs text-amber-600 border-amber-300">
                    <Coffee className="h-3 w-3 mr-1" />
                    Fasting Required
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Patient should fast for 8-12 hours before this test</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
          <span>CPT: {test.cptCode}</span>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {test.turnaroundTime}
          </span>
          <span className="text-green-600 font-medium">${(test.price ?? 0).toFixed(2)}</span>
        </div>
        {showInstructions && (
          <Textarea
            placeholder="Special instructions for this test..."
            value={test.specialInstructions || ""}
            onChange={(e) => onUpdateInstructions(e.target.value)}
            className="mt-2 text-xs h-16"
          />
        )}
        <Button
          variant="ghost"
          size="sm"
          className="mt-1 h-6 text-xs"
          onClick={() => setShowInstructions(!showInstructions)}
        >
          {showInstructions ? "Hide" : "Add"} special instructions
        </Button>
      </div>
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-destructive hover:text-destructive"
        onClick={onRemove}
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

// Diagnosis Code Selector
interface DiagnosisCodeSelectorProps {
  selectedCodes: DiagnosisCode[];
  onSelect: (code: DiagnosisCode) => void;
  onRemove: (code: string) => void;
}

function DiagnosisCodeSelector({ selectedCodes, onSelect, onRemove }: DiagnosisCodeSelectorProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const filteredCodes = COMMON_DIAGNOSIS_CODES.filter(
    (code) =>
      !selectedCodes.find((s) => s.code === code.code) &&
      (code.code.toLowerCase().includes(search.toLowerCase()) ||
        code.description.toLowerCase().includes(search.toLowerCase()))
  );

  const groupedCodes = filteredCodes.reduce((acc, code) => {
    const category = code.category || "Other";
    if (!acc[category]) acc[category] = [];
    acc[category].push(code);
    return acc;
  }, {} as Record<string, DiagnosisCode[]>);

  return (
    <div className="space-y-2">
      <Label className="flex items-center gap-2">
        <FileText className="h-4 w-4" />
        Diagnosis Codes (ICD-10)
      </Label>

      {/* Selected Codes */}
      {selectedCodes.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selectedCodes.map((code) => (
            <Badge
              key={code.code}
              variant="secondary"
              className="flex items-center gap-1 py-1"
            >
              <span className="font-mono">{code.code}</span>
              <span className="text-muted-foreground">-</span>
              <span className="truncate max-w-[200px]">{code.description}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 ml-1"
                onClick={() => onRemove(code.code)}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          ))}
        </div>
      )}

      {/* Code Search */}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="w-full justify-start text-muted-foreground">
            <Search className="mr-2 h-4 w-4" />
            Search diagnosis codes...
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[500px] p-0" align="start">
          <Command>
            <CommandInput
              placeholder="Search by code or description..."
              value={search}
              onValueChange={setSearch}
            />
            <CommandList>
              <CommandEmpty>No matching codes found.</CommandEmpty>
              {Object.entries(groupedCodes).map(([category, codes]) => (
                <CommandGroup key={category} heading={category}>
                  {codes.map((code) => (
                    <CommandItem
                      key={code.code}
                      onSelect={() => {
                        onSelect(code);
                        setOpen(false);
                        setSearch("");
                      }}
                      className="flex items-center gap-2"
                    >
                      <span className="font-mono text-primary">{code.code}</span>
                      <span className="flex-1 truncate">{code.description}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              ))}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
      <p className="text-xs text-muted-foreground">
        At least one diagnosis code is required for insurance billing
      </p>
    </div>
  );
}

// Facility Selector
interface FacilitySelectorProps {
  selectedFacility: LabFacility | null;
  onSelect: (facility: LabFacility) => void;
  patientInsurance?: string;
}

function FacilitySelector({ selectedFacility, onSelect, patientInsurance }: FacilitySelectorProps) {
  return (
    <div className="space-y-3">
      <Label className="flex items-center gap-2">
        <Building2 className="h-4 w-4" />
        Lab Facility
      </Label>
      <RadioGroup
        value={selectedFacility?.id || ""}
        onValueChange={(value) => {
          const facility = LAB_FACILITIES.find((f) => f.id === value);
          if (facility) onSelect(facility);
        }}
        className="space-y-2"
      >
        {LAB_FACILITIES.map((facility) => {
          const acceptsInsurance = patientInsurance
            ? (facility.acceptedInsurance ?? []).includes(patientInsurance) ||
              (facility.acceptedInsurance ?? []).includes("All insurances")
            : true;

          return (
            <div
              key={facility.id}
              className={cn(
                "flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors",
                selectedFacility?.id === facility.id && "border-primary bg-primary/5"
              )}
              onClick={() => onSelect(facility)}
            >
              <RadioGroupItem value={facility.id} className="mt-1" />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{facility.name}</span>
                  {facility.electronicOrdering && (
                    <Badge variant="secondary" className="text-xs">
                      <Send className="h-3 w-3 mr-1" />
                      e-Order
                    </Badge>
                  )}
                  {!acceptsInsurance && (
                    <Badge variant="destructive" className="text-xs">
                      Out of Network
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                  <MapPin className="h-3 w-3" />
                  {facility.address}, {facility.city}
                </div>
                <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    ~{facility.averageWaitTime} min wait
                  </span>
                  <span>{facility.operatingHours}</span>
                </div>
              </div>
            </div>
          );
        })}
      </RadioGroup>
    </div>
  );
}

// Fasting Alert
interface FastingAlertProps {
  testsRequiringFasting: SelectedTest[];
}

function FastingAlert({ testsRequiringFasting }: FastingAlertProps) {
  if (testsRequiringFasting.length === 0) return null;

  return (
    <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
      <Coffee className="h-5 w-5 text-amber-600 mt-0.5" />
      <div>
        <h4 className="font-medium text-amber-800">Fasting Required</h4>
        <p className="text-sm text-amber-700 mt-1">
          The following tests require fasting (8-12 hours, water only):
        </p>
        <ul className="list-disc list-inside mt-2 text-sm text-amber-700">
          {testsRequiringFasting.map((test) => (
            <li key={test.id}>{test.name}</li>
          ))}
        </ul>
        <p className="text-xs text-amber-600 mt-2">
          Patient should be instructed to fast before specimen collection.
        </p>
      </div>
    </div>
  );
}

// Order Summary
interface OrderSummaryProps {
  selectedTests: SelectedTest[];
  selectedPanels: string[];
  priority: string;
  facility: LabFacility | null;
  diagnosisCodes: DiagnosisCode[];
}

function OrderSummary({
  selectedTests,
  selectedPanels,
  priority,
  facility,
  diagnosisCodes,
}: OrderSummaryProps) {
  const totalPrice = selectedTests.reduce((sum, test) => sum + (test.price ?? 0), 0);
  const hasAnyFasting = selectedTests.some((t) => t.requiresFasting);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <FileText className="h-4 w-4" />
          Order Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Tests</span>
          <span className="font-medium">{selectedTests.length}</span>
        </div>
        {selectedPanels.length > 0 && (
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Panels</span>
            <span className="font-medium">{selectedPanels.length}</span>
          </div>
        )}
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Priority</span>
          <Badge
            variant={
              priority === "stat"
                ? "destructive"
                : priority === "urgent"
                ? "default"
                : "secondary"
            }
          >
            {priority.charAt(0).toUpperCase() + priority.slice(1)}
          </Badge>
        </div>
        {facility && (
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Facility</span>
            <span className="font-medium text-right max-w-[150px] truncate">
              {facility.name}
            </span>
          </div>
        )}
        {hasAnyFasting && (
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Fasting</span>
            <Badge variant="outline" className="text-amber-600">
              <Coffee className="h-3 w-3 mr-1" />
              Required
            </Badge>
          </div>
        )}
        <Separator />
        <div className="flex justify-between text-sm font-medium">
          <span>Estimated Cost</span>
          <span className="text-green-600">${totalPrice.toFixed(2)}</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Final cost depends on insurance coverage and facility pricing.
        </p>
        {diagnosisCodes.length === 0 && (
          <div className="flex items-center gap-2 text-xs text-amber-600">
            <AlertTriangle className="h-3 w-3" />
            Diagnosis code required for submission
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function LabOrderForm({
  patientId,
  patientName,
  patientDOB,
  patientInsurance,
  onSubmit,
  onCancel,
}: LabOrderFormProps) {
  // State
  const [selectedTests, setSelectedTests] = useState<SelectedTest[]>([]);
  const [selectedPanels, setSelectedPanels] = useState<string[]>([]);
  const [priority, setPriority] = useState<"routine" | "urgent" | "stat">("routine");
  const [collectionType, setCollectionType] = useState<"in-office" | "psc" | "mobile">("psc");
  const [selectedFacility, setSelectedFacility] = useState<LabFacility | null>(null);
  const [diagnosisCodes, setDiagnosisCodes] = useState<DiagnosisCode[]>([]);
  const [clinicalNotes, setClinicalNotes] = useState("");
  const [scheduledDate, setScheduledDate] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Store
  const { createLabOrder, labTests } = useClinicalWorkflowsStore();

  // Computed
  const testsRequiringFasting = useMemo(
    () => selectedTests.filter((t) => t.requiresFasting),
    [selectedTests]
  );

  const canSubmit = selectedTests.length > 0 && diagnosisCodes.length > 0 && selectedFacility;

  // Handlers
  const handleAddTest = useCallback((test: LabTest) => {
    setSelectedTests((prev) => [...prev, { ...test }]);
  }, []);

  const handleRemoveTest = useCallback((testId: string) => {
    setSelectedTests((prev) => prev.filter((t) => t.id !== testId));
  }, []);

  const handleUpdateTestInstructions = useCallback(
    (testId: string, instructions: string) => {
      setSelectedTests((prev) =>
        prev.map((t) =>
          t.id === testId ? { ...t, specialInstructions: instructions } : t
        )
      );
    },
    []
  );

  const handleTogglePanel = useCallback(
    (panelId: string) => {
      const panel = LAB_PANELS.find((p) => p.id === panelId);
      if (!panel) return;

      if (selectedPanels.includes(panelId)) {
        // Remove panel and its tests
        setSelectedPanels((prev) => prev.filter((id) => id !== panelId));
        // Keep tests that aren't part of this panel
        setSelectedTests((prev) =>
          prev.filter((t) => !panel.tests.includes(t.id))
        );
      } else {
        // Add panel
        setSelectedPanels((prev) => [...prev, panelId]);
        // Add panel tests that aren't already selected
        const panelTests = labTests.filter(
          (t) =>
            panel.tests.includes(t.id) &&
            !selectedTests.find((st) => st.id === t.id)
        );
        setSelectedTests((prev) => [...prev, ...panelTests]);
      }
    },
    [selectedPanels, selectedTests, labTests]
  );

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;

    setIsSubmitting(true);
    try {
      const order: Partial<LabOrder> = {
        patientId,
        tests: selectedTests,
        priority,
        collectionType,
        facility: selectedFacility!,
        diagnosis: diagnosisCodes,
        clinicalNotes,
        scheduledDate: scheduledDate || undefined,
        status: "pending",
        orderedAt: new Date().toISOString(),
      };

      createLabOrder(order as LabOrder);
      onSubmit(order);
    } finally {
      setIsSubmitting(false);
    }
  }, [
    canSubmit,
    patientId,
    selectedTests,
    priority,
    collectionType,
    selectedFacility,
    diagnosisCodes,
    clinicalNotes,
    scheduledDate,
    createLabOrder,
    onSubmit,
  ]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Beaker className="h-5 w-5 text-primary" />
            New Lab Order
          </h2>
          <p className="text-sm text-muted-foreground">
            Patient: <span className="font-medium">{patientName}</span>
            {patientDOB && <span className="ml-2">DOB: {patientDOB}</span>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            disabled={!canSubmit || isSubmitting}
            onClick={() => setShowConfirmDialog(true)}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Submit Order
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <div className="flex h-full">
          {/* Main Form */}
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-6 max-w-3xl">
              {/* Test Panels */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Quick Order - Common Panels
                </Label>
                <div className="grid grid-cols-2 gap-2">
                  {LAB_PANELS.map((panel) => (
                    <PanelCard
                      key={panel.id}
                      panel={panel}
                      isSelected={selectedPanels.includes(panel.id)}
                      onToggle={() => handleTogglePanel(panel.id)}
                    />
                  ))}
                </div>
              </div>

              <Separator />

              {/* Individual Test Search */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2">
                  <Search className="h-4 w-4" />
                  Add Individual Tests
                </Label>
                <TestSearch
                  onSelectTest={handleAddTest}
                  selectedTestIds={selectedTests.map((t) => t.id)}
                />
              </div>

              {/* Selected Tests */}
              {selectedTests.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Selected Tests ({selectedTests.length})</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive"
                      onClick={() => {
                        setSelectedTests([]);
                        setSelectedPanels([]);
                      }}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Clear All
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {selectedTests.map((test) => (
                      <SelectedTestItem
                        key={test.id}
                        test={test}
                        onRemove={() => handleRemoveTest(test.id)}
                        onUpdateInstructions={(instructions) =>
                          handleUpdateTestInstructions(test.id, instructions)
                        }
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Fasting Alert */}
              <FastingAlert testsRequiringFasting={testsRequiringFasting} />

              <Separator />

              {/* Order Details */}
              <div className="grid grid-cols-2 gap-4">
                {/* Priority */}
                <div className="space-y-2">
                  <Label>Priority</Label>
                  <Select value={priority} onValueChange={(v: "routine" | "urgent" | "stat") => setPriority(v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="routine">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-gray-400" />
                          Routine (24-72 hrs)
                        </div>
                      </SelectItem>
                      <SelectItem value="urgent">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-amber-500" />
                          Urgent (Same day)
                        </div>
                      </SelectItem>
                      <SelectItem value="stat">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-red-500" />
                          STAT (1-2 hrs)
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Collection Type */}
                <div className="space-y-2">
                  <Label>Collection Type</Label>
                  <Select
                    value={collectionType}
                    onValueChange={(v: "in-office" | "psc" | "mobile") => setCollectionType(v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="in-office">In-Office Draw</SelectItem>
                      <SelectItem value="psc">Patient Service Center</SelectItem>
                      <SelectItem value="mobile">Mobile Phlebotomy</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Scheduled Date */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Scheduled Date (Optional)
                </Label>
                <Input
                  type="date"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                  min={format(new Date(), "yyyy-MM-dd")}
                />
                <p className="text-xs text-muted-foreground">
                  Leave blank if patient can go anytime
                </p>
              </div>

              <Separator />

              {/* Diagnosis Codes */}
              <DiagnosisCodeSelector
                selectedCodes={diagnosisCodes}
                onSelect={(code) => setDiagnosisCodes([...diagnosisCodes, code])}
                onRemove={(code) =>
                  setDiagnosisCodes(diagnosisCodes.filter((c) => c.code !== code))
                }
              />

              <Separator />

              {/* Facility Selection */}
              <FacilitySelector
                selectedFacility={selectedFacility}
                onSelect={setSelectedFacility}
                patientInsurance={patientInsurance?.provider}
              />

              <Separator />

              {/* Clinical Notes */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Clinical Notes (Optional)
                </Label>
                <Textarea
                  placeholder="Additional clinical information for the lab..."
                  value={clinicalNotes}
                  onChange={(e) => setClinicalNotes(e.target.value)}
                  className="h-24"
                />
              </div>
            </div>
          </ScrollArea>

          {/* Order Summary Sidebar */}
          <div className="w-72 border-l bg-muted/30 p-4">
            <OrderSummary
              selectedTests={selectedTests}
              selectedPanels={selectedPanels}
              priority={priority}
              facility={selectedFacility}
              diagnosisCodes={diagnosisCodes}
            />

            {/* Quick Actions */}
            <div className="mt-4 space-y-2">
              <Button variant="outline" className="w-full justify-start" size="sm">
                <Star className="h-4 w-4 mr-2" />
                Save as Favorite Order
              </Button>
              <Button variant="outline" className="w-full justify-start" size="sm">
                <Printer className="h-4 w-4 mr-2" />
                Print Requisition
              </Button>
            </div>

            {/* Insurance Info */}
            {patientInsurance && (
              <Card className="mt-4">
                <CardHeader className="py-3 px-4">
                  <CardTitle className="text-xs font-medium text-muted-foreground">
                    Insurance
                  </CardTitle>
                </CardHeader>
                <CardContent className="py-0 px-4 pb-3">
                  <p className="text-sm font-medium">{patientInsurance.provider}</p>
                  <p className="text-xs text-muted-foreground">
                    ID: {patientInsurance.memberId}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Lab Order</DialogTitle>
            <DialogDescription>
              Please review the order details before submitting.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Patient</h4>
              <p className="text-sm text-muted-foreground">{patientName}</p>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium">Tests ({selectedTests.length})</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                {selectedTests.slice(0, 5).map((test) => (
                  <li key={test.id} className="flex items-center gap-2">
                    <Beaker className="h-3 w-3" />
                    {test.name}
                  </li>
                ))}
                {selectedTests.length > 5 && (
                  <li className="text-xs">
                    +{selectedTests.length - 5} more tests
                  </li>
                )}
              </ul>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium">Facility</h4>
              <p className="text-sm text-muted-foreground">
                {selectedFacility?.name}
              </p>
            </div>

            {testsRequiringFasting.length > 0 && (
              <div className="flex items-center gap-2 p-3 bg-amber-50 rounded-lg">
                <Coffee className="h-4 w-4 text-amber-600" />
                <span className="text-sm text-amber-800">
                  Patient will be notified about fasting requirements
                </span>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  Confirm & Submit
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ============================================================================
// Compact Lab Order Widget
// ============================================================================

interface LabOrderWidgetProps {
  patientId: string;
  recentOrders?: LabOrder[];
  onNewOrder: () => void;
}

export function LabOrderWidget({ patientId, recentOrders = [], onNewOrder }: LabOrderWidgetProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Beaker className="h-4 w-4" />
            Lab Orders
          </CardTitle>
          <Button size="sm" onClick={onNewOrder}>
            <Plus className="h-4 w-4 mr-1" />
            New Order
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {recentOrders.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground">
            <Beaker className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No recent lab orders</p>
          </div>
        ) : (
          <div className="space-y-2">
            {recentOrders.slice(0, 3).map((order) => (
              <div
                key={order.id}
                className="flex items-center justify-between p-2 bg-muted/30 rounded-lg"
              >
                <div>
                  <p className="text-sm font-medium">
                    {order.tests.length} test{order.tests.length !== 1 ? "s" : ""}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {format(new Date(order.orderedAt || Date.now()), "MMM d, yyyy")}
                  </p>
                </div>
                <Badge
                  variant={
                    order.status === "completed"
                      ? "default"
                      : order.status === "collected"
                      ? "secondary"
                      : "outline"
                  }
                >
                  {order.status}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Lab Order Skeleton
// ============================================================================

export function LabOrderFormSkeleton() {
  return (
    <div className="animate-pulse space-y-4 p-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-6 w-48 bg-muted rounded" />
          <div className="h-4 w-32 bg-muted rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-9 w-20 bg-muted rounded" />
          <div className="h-9 w-28 bg-muted rounded" />
        </div>
      </div>

      <div className="h-px bg-muted" />

      <div className="space-y-3">
        <div className="h-4 w-32 bg-muted rounded" />
        <div className="grid grid-cols-2 gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-muted rounded-lg" />
          ))}
        </div>
      </div>

      <div className="h-px bg-muted" />

      <div className="h-10 w-full bg-muted rounded" />

      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-16 bg-muted rounded-lg" />
        ))}
      </div>
    </div>
  );
}

export default LabOrderForm;
