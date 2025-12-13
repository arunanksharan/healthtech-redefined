"use client";

// Referral Creation Form Component
// EPIC-UX-007: Clinical Workflows Interface - Journey 7.5 Specialist Referrals

import React, { useState, useCallback, useMemo } from "react";
import { format } from "date-fns";
import {
  Search,
  User,
  Building2,
  MapPin,
  Phone,
  Mail,
  Calendar,
  Clock,
  Star,
  StarOff,
  FileText,
  Paperclip,
  Upload,
  Send,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  X,
  Plus,
  Wand2,
  ChevronRight,
  ExternalLink,
  Shield,
  CreditCard,
  Stethoscope,
  ArrowRight,
  Info,
  MessageSquare,
  Globe,
  Award,
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
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Progress } from "@/components/ui/progress";
import {
  useClinicalWorkflowsStore,
  type Referral,
  type Specialist,
  type AttachedDocument,
} from "@/lib/store/clinical-workflows-store";

// ============================================================================
// Types
// ============================================================================

interface ReferralFormProps {
  patientId: string;
  patientName: string;
  patientDOB?: string;
  patientInsurance?: {
    provider: string;
    memberId: string;
    requiresAuth: boolean;
  };
  recentDiagnoses?: { code: string; description: string }[];
  onSubmit: (referral: Partial<Referral>) => void;
  onCancel: () => void;
}

interface SpecialtyCategory {
  id: string;
  name: string;
  specialties: string[];
}

// ============================================================================
// Mock Data
// ============================================================================

const SPECIALTY_CATEGORIES: SpecialtyCategory[] = [
  {
    id: "cat-primary",
    name: "Primary Care",
    specialties: ["Family Medicine", "Internal Medicine", "Geriatrics"],
  },
  {
    id: "cat-cardio",
    name: "Cardiovascular",
    specialties: ["Cardiology", "Cardiac Surgery", "Vascular Surgery"],
  },
  {
    id: "cat-ortho",
    name: "Orthopedics",
    specialties: ["Orthopedic Surgery", "Sports Medicine", "Physical Medicine"],
  },
  {
    id: "cat-neuro",
    name: "Neurology",
    specialties: ["Neurology", "Neurosurgery", "Pain Management"],
  },
  {
    id: "cat-gi",
    name: "Gastroenterology",
    specialties: ["Gastroenterology", "Hepatology", "Colorectal Surgery"],
  },
  {
    id: "cat-endo",
    name: "Endocrinology",
    specialties: ["Endocrinology", "Diabetology"],
  },
  {
    id: "cat-pulm",
    name: "Pulmonology",
    specialties: ["Pulmonology", "Thoracic Surgery", "Sleep Medicine"],
  },
  {
    id: "cat-onc",
    name: "Oncology",
    specialties: ["Medical Oncology", "Surgical Oncology", "Radiation Oncology"],
  },
  {
    id: "cat-psych",
    name: "Psychiatry",
    specialties: ["Psychiatry", "Psychology", "Addiction Medicine"],
  },
  {
    id: "cat-derm",
    name: "Dermatology",
    specialties: ["Dermatology", "Dermatologic Surgery"],
  },
];

const REFERRAL_REASONS: { specialty: string; reasons: string[] }[] = [
  {
    specialty: "Cardiology",
    reasons: [
      "Evaluation of chest pain",
      "Management of heart failure",
      "Arrhythmia evaluation",
      "Pre-operative cardiac clearance",
      "Hypertension management",
      "Echocardiogram interpretation",
    ],
  },
  {
    specialty: "Orthopedic Surgery",
    reasons: [
      "Chronic joint pain evaluation",
      "Post-injury assessment",
      "Surgical consultation",
      "Arthritis management",
      "Back pain evaluation",
      "Sports injury",
    ],
  },
  {
    specialty: "Gastroenterology",
    reasons: [
      "GERD/heartburn management",
      "Colonoscopy screening",
      "Liver function abnormality",
      "Abdominal pain evaluation",
      "Inflammatory bowel disease",
      "Hepatitis management",
    ],
  },
  {
    specialty: "Endocrinology",
    reasons: [
      "Diabetes management",
      "Thyroid disorder evaluation",
      "Osteoporosis management",
      "Hormone imbalance",
      "Adrenal disorder",
      "Metabolic disorder",
    ],
  },
  {
    specialty: "Neurology",
    reasons: [
      "Headache/migraine evaluation",
      "Seizure disorder",
      "Memory concerns",
      "Neuropathy evaluation",
      "Movement disorder",
      "Stroke follow-up",
    ],
  },
];

// ============================================================================
// Sub-Components
// ============================================================================

// Specialist Search
interface SpecialistSearchProps {
  specialty?: string;
  onSelect: (specialist: Specialist) => void;
  patientInsurance?: string;
}

function SpecialistSearch({ specialty, onSelect, patientInsurance }: SpecialistSearchProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { specialists, searchSpecialists, isLoadingSpecialists } = useClinicalWorkflowsStore();

  const handleSearch = useCallback(
    (value: string) => {
      setSearch(value);
      if (value.length >= 2 || specialty) {
        searchSpecialists(value, specialty);
      }
    },
    [searchSpecialists, specialty]
  );

  // Filter and sort specialists
  const sortedSpecialists = useMemo(() => {
    return [...specialists].sort((a, b) => {
      // In-network first
      const aInNetwork = patientInsurance ? (a.insuranceAccepted ?? []).includes(patientInsurance) : true;
      const bInNetwork = patientInsurance ? (b.insuranceAccepted ?? []).includes(patientInsurance) : true;
      if (aInNetwork !== bInNetwork) return aInNetwork ? -1 : 1;

      // Then by rating
      return (b.rating ?? 0) - (a.rating ?? 0);
    });
  }, [specialists, patientInsurance]);

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
          Search specialists by name or practice...
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[600px] p-0" align="start">
        <Command>
          <CommandInput
            placeholder={`Search ${specialty || "specialists"}...`}
            value={search}
            onValueChange={handleSearch}
          />
          <CommandList>
            <CommandEmpty>
              {isLoadingSpecialists ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Searching...
                </div>
              ) : (
                <div className="py-4 text-center">
                  <p className="text-sm text-muted-foreground">No specialists found</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Try adjusting your search criteria
                  </p>
                </div>
              )}
            </CommandEmpty>
            <CommandGroup heading="Available Specialists">
              {sortedSpecialists.map((specialist) => {
                const isInNetwork = patientInsurance
                  ? (specialist.insuranceAccepted ?? []).includes(patientInsurance)
                  : true;

                return (
                  <CommandItem
                    key={specialist.id}
                    onSelect={() => {
                      onSelect(specialist);
                      setOpen(false);
                      setSearch("");
                    }}
                    className="flex items-start gap-3 py-3"
                  >
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <User className="h-5 w-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{specialist.name}</span>
                        {isInNetwork ? (
                          <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                            <Shield className="h-3 w-3 mr-1" />
                            In-Network
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs text-amber-600">
                            Out of Network
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {specialist.specialty}
                      </p>
                      <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3 w-3" />
                          {specialist.practice}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {specialist.distance} mi
                        </span>
                        <span className="flex items-center gap-1">
                          <Star className="h-3 w-3 text-amber-500 fill-amber-500" />
                          {(specialist.rating ?? 0).toFixed(1)}
                        </span>
                        {specialist.nextAvailable && (
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            Next: {specialist.nextAvailable}
                          </span>
                        )}
                      </div>
                    </div>
                  </CommandItem>
                );
              })}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

// Selected Specialist Card
interface SelectedSpecialistCardProps {
  specialist: Specialist;
  onRemove: () => void;
  isInNetwork: boolean;
}

function SelectedSpecialistCard({ specialist, onRemove, isInNetwork }: SelectedSpecialistCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
            <User className="h-6 w-6 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h4 className="font-medium">{specialist.name}</h4>
                {isInNetwork ? (
                  <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                    <Shield className="h-3 w-3 mr-1" />
                    In-Network
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-xs text-amber-600">
                    Out of Network
                  </Badge>
                )}
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={onRemove}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">{specialist.specialty}</p>
            <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-muted-foreground" />
                <span>{specialist.practice}</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <span>{specialist.address}</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <span>{specialist.phone}</span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <span className="truncate">{specialist.email}</span>
              </div>
            </div>
            <div className="flex items-center gap-4 mt-3">
              <div className="flex items-center gap-1">
                <Star className="h-4 w-4 text-amber-500 fill-amber-500" />
                <span className="font-medium">{(specialist.rating ?? 0).toFixed(1)}</span>
                <span className="text-xs text-muted-foreground">
                  ({specialist.reviewCount} reviews)
                </span>
              </div>
              {specialist.acceptingNewPatients && (
                <Badge variant="secondary" className="text-xs">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Accepting New Patients
                </Badge>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Reason for Referral Selector
interface ReasonSelectorProps {
  specialty?: string;
  value: string;
  onChange: (value: string) => void;
}

function ReasonSelector({ specialty, value, onChange }: ReasonSelectorProps) {
  const [customReason, setCustomReason] = useState(false);

  const suggestedReasons = useMemo(() => {
    const match = REFERRAL_REASONS.find(
      (r) => specialty?.toLowerCase().includes(r.specialty.toLowerCase())
    );
    return match?.reasons || [];
  }, [specialty]);

  if (customReason || suggestedReasons.length === 0) {
    return (
      <div className="space-y-2">
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Enter the reason for referral..."
          className="min-h-[100px]"
        />
        {suggestedReasons.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCustomReason(false)}
          >
            Show suggested reasons
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        {suggestedReasons.map((reason) => (
          <Button
            key={reason}
            variant={value === reason ? "default" : "outline"}
            className="justify-start h-auto py-2 px-3 text-left"
            onClick={() => onChange(reason)}
          >
            <span className="text-sm">{reason}</span>
          </Button>
        ))}
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="text-primary"
        onClick={() => setCustomReason(true)}
      >
        <Plus className="h-4 w-4 mr-1" />
        Enter custom reason
      </Button>
    </div>
  );
}

// Document Attachment
interface DocumentAttachmentProps {
  documents: AttachedDocument[];
  onAdd: (doc: AttachedDocument) => void;
  onRemove: (docId: string) => void;
}

function DocumentAttachment({ documents, onAdd, onRemove }: DocumentAttachmentProps) {
  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        const doc: AttachedDocument = {
          id: `doc-${Date.now()}`,
          name: file.name,
          type: file.type.includes("pdf") ? "pdf" : "image",
          size: file.size,
          uploadedAt: new Date().toISOString(),
        };
        onAdd(doc);
      }
      e.target.value = "";
    },
    [onAdd]
  );

  return (
    <div className="space-y-3">
      <Label className="flex items-center gap-2">
        <Paperclip className="h-4 w-4" />
        Attached Documents
      </Label>

      {documents.length > 0 && (
        <div className="space-y-2">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-2 bg-muted/50 rounded-lg"
            >
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">{doc.name}</span>
                <Badge variant="secondary" className="text-xs">
                  {doc.size}
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => onRemove(doc.id)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      )}

      <div className="border-2 border-dashed rounded-lg p-4 text-center hover:bg-muted/50 transition-colors">
        <input
          type="file"
          id="referral-file-upload"
          className="hidden"
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={handleFileSelect}
        />
        <label htmlFor="referral-file-upload" className="cursor-pointer">
          <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
          <p className="text-sm font-medium">Drop files here or click to upload</p>
          <p className="text-xs text-muted-foreground mt-1">
            PDF, PNG, JPG up to 10MB
          </p>
        </label>
      </div>

      {/* Quick Add Buttons */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            onAdd({
              id: `doc-${Date.now()}`,
              name: "Recent Lab Results",
              type: "lab_result",
              size: 128000,
              uploadedAt: new Date().toISOString(),
            })
          }
        >
          <Plus className="h-3 w-3 mr-1" />
          Lab Results
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            onAdd({
              id: `doc-${Date.now()}`,
              name: "Imaging Report",
              type: "imaging",
              size: 2200000,
              uploadedAt: new Date().toISOString(),
            })
          }
        >
          <Plus className="h-3 w-3 mr-1" />
          Imaging
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            onAdd({
              id: `doc-${Date.now()}`,
              name: "Clinical Summary",
              type: "clinical_summary",
              size: 87000,
              uploadedAt: new Date().toISOString(),
            })
          }
        >
          <Plus className="h-3 w-3 mr-1" />
          Clinical Summary
        </Button>
      </div>
    </div>
  );
}

// Insurance Authorization Check
interface AuthorizationCheckProps {
  requiresAuth: boolean;
  status: "pending" | "approved" | "denied" | "not_required";
  onCheck: () => void;
}

function AuthorizationCheck({ requiresAuth, status, onCheck }: AuthorizationCheckProps) {
  if (!requiresAuth) {
    return (
      <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
        <CheckCircle2 className="h-5 w-5 text-green-600" />
        <div>
          <p className="text-sm font-medium text-green-800">
            No Prior Authorization Required
          </p>
          <p className="text-xs text-green-700">
            This referral does not require insurance pre-authorization.
          </p>
        </div>
      </div>
    );
  }

  const statusConfig = {
    pending: {
      icon: <Clock className="h-5 w-5 text-amber-600" />,
      bg: "bg-amber-50 border-amber-200",
      title: "Authorization Pending",
      description: "Prior authorization is being processed.",
      textColor: "text-amber-800",
      descColor: "text-amber-700",
    },
    approved: {
      icon: <CheckCircle2 className="h-5 w-5 text-green-600" />,
      bg: "bg-green-50 border-green-200",
      title: "Authorization Approved",
      description: "Prior authorization has been approved.",
      textColor: "text-green-800",
      descColor: "text-green-700",
    },
    denied: {
      icon: <AlertTriangle className="h-5 w-5 text-red-600" />,
      bg: "bg-red-50 border-red-200",
      title: "Authorization Denied",
      description: "Prior authorization was denied. Appeal may be required.",
      textColor: "text-red-800",
      descColor: "text-red-700",
    },
    not_required: {
      icon: <Info className="h-5 w-5 text-blue-600" />,
      bg: "bg-blue-50 border-blue-200",
      title: "Check Authorization Status",
      description: "Click to verify if prior authorization is needed.",
      textColor: "text-blue-800",
      descColor: "text-blue-700",
    },
  };

  const config = statusConfig[status];

  return (
    <div className={cn("flex items-center gap-3 p-3 border rounded-lg", config.bg)}>
      {config.icon}
      <div className="flex-1">
        <p className={cn("text-sm font-medium", config.textColor)}>{config.title}</p>
        <p className={cn("text-xs", config.descColor)}>{config.description}</p>
      </div>
      {status === "not_required" && (
        <Button size="sm" variant="outline" onClick={onCheck}>
          Check Now
        </Button>
      )}
    </div>
  );
}

// Referral Summary Card
interface ReferralSummaryProps {
  specialist: Specialist | null;
  referralType: string;
  priority: string;
  reason: string;
  documents: AttachedDocument[];
}

function ReferralSummary({
  specialist,
  referralType,
  priority,
  reason,
  documents,
}: ReferralSummaryProps) {
  const completionItems = [
    { label: "Specialist selected", done: !!specialist },
    { label: "Referral type", done: !!referralType },
    { label: "Priority set", done: !!priority },
    { label: "Reason provided", done: reason.length > 10 },
  ];

  const completedCount = completionItems.filter((i) => i.done).length;
  const progress = (completedCount / completionItems.length) * 100;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <FileText className="h-4 w-4" />
          Referral Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Completion</span>
            <span>{completedCount}/{completionItems.length}</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        <div className="space-y-2">
          {completionItems.map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              {item.done ? (
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              ) : (
                <div className="h-4 w-4 rounded-full border-2" />
              )}
              <span className={item.done ? "" : "text-muted-foreground"}>
                {item.label}
              </span>
            </div>
          ))}
        </div>

        <Separator />

        {specialist && (
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Referring To</p>
            <p className="text-sm font-medium">{specialist.name}</p>
            <p className="text-xs text-muted-foreground">{specialist.specialty}</p>
          </div>
        )}

        {documents.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Attachments</p>
            <p className="text-sm">{documents.length} document(s)</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function ReferralForm({
  patientId,
  patientName,
  patientDOB,
  patientInsurance,
  recentDiagnoses = [],
  onSubmit,
  onCancel,
}: ReferralFormProps) {
  // State
  const [selectedSpecialty, setSelectedSpecialty] = useState<string>("");
  const [selectedSpecialist, setSelectedSpecialist] = useState<Specialist | null>(null);
  const [referralType, setReferralType] = useState<"consultation" | "transfer" | "co-management">("consultation");
  const [priority, setPriority] = useState<"routine" | "urgent" | "emergent">("routine");
  const [reasonForReferral, setReasonForReferral] = useState("");
  const [clinicalSummary, setClinicalSummary] = useState("");
  const [patientPreferences, setPatientPreferences] = useState("");
  const [documents, setDocuments] = useState<AttachedDocument[]>([]);
  const [includeLabResults, setIncludeLabResults] = useState(true);
  const [includeMedications, setIncludeMedications] = useState(true);
  const [authStatus, setAuthStatus] = useState<"pending" | "approved" | "denied" | "not_required">("not_required");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);

  // Store
  const { createReferral, generateReferralLetter } = useClinicalWorkflowsStore();

  // Computed
  const isInNetwork = patientInsurance && selectedSpecialist
    ? (selectedSpecialist.insuranceAccepted ?? []).includes(patientInsurance.provider)
    : true;

  const canSubmit = selectedSpecialist && reasonForReferral.length > 10;

  // Handlers
  const handleGenerateSummary = useCallback(async () => {
    setIsGeneratingAI(true);
    try {
      // Simulate AI generation
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const summary = `Clinical Summary for ${patientName}

Patient presents with ${reasonForReferral || "[reason for referral]"}.

Relevant History:
${recentDiagnoses.length > 0
  ? recentDiagnoses.map(d => `- ${d.code}: ${d.description}`).join("\n")
  : "- No significant past medical history documented"
}

Current Status:
- Patient is stable and appropriate for outpatient referral
- ${includeLabResults ? "Recent lab results attached" : "Labs not included"}
- ${includeMedications ? "Current medication list attached" : "Medications not included"}

Request:
Please evaluate and provide recommendations for management. Patient ${patientPreferences ? `prefers ${patientPreferences}` : "has no specific preferences regarding appointment timing"}.`;

      setClinicalSummary(summary);
    } finally {
      setIsGeneratingAI(false);
    }
  }, [patientName, reasonForReferral, recentDiagnoses, includeLabResults, includeMedications, patientPreferences]);

  const handleCheckAuth = useCallback(() => {
    // Simulate auth check
    setAuthStatus("pending");
    setTimeout(() => {
      setAuthStatus(Math.random() > 0.3 ? "approved" : "pending");
    }, 2000);
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!canSubmit || !selectedSpecialist) return;

    setIsSubmitting(true);
    try {
      const referral: Partial<Referral> = {
        patientId,
        specialist: selectedSpecialist,
        referralType,
        priority,
        reasonForReferral,
        clinicalSummary,
        attachedDocuments: documents,
        status: "sent",
        createdAt: new Date().toISOString(),
      };

      createReferral(referral as Referral);
      onSubmit(referral);
    } finally {
      setIsSubmitting(false);
    }
  }, [
    canSubmit,
    patientId,
    selectedSpecialist,
    referralType,
    priority,
    reasonForReferral,
    clinicalSummary,
    documents,
    createReferral,
    onSubmit,
  ]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Send className="h-5 w-5 text-primary" />
            New Referral
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
                Sending...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Send Referral
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
              {/* Specialty Selection */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2">
                  <Stethoscope className="h-4 w-4" />
                  Specialty
                </Label>
                <Select value={selectedSpecialty} onValueChange={setSelectedSpecialty}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a specialty" />
                  </SelectTrigger>
                  <SelectContent>
                    {SPECIALTY_CATEGORIES.map((category) => (
                      <div key={category.id}>
                        <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground">
                          {category.name}
                        </div>
                        {category.specialties.map((specialty) => (
                          <SelectItem key={specialty} value={specialty}>
                            {specialty}
                          </SelectItem>
                        ))}
                      </div>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Specialist Search */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Specialist
                </Label>
                {selectedSpecialist ? (
                  <SelectedSpecialistCard
                    specialist={selectedSpecialist}
                    onRemove={() => setSelectedSpecialist(null)}
                    isInNetwork={isInNetwork}
                  />
                ) : (
                  <SpecialistSearch
                    specialty={selectedSpecialty}
                    onSelect={setSelectedSpecialist}
                    patientInsurance={patientInsurance?.provider}
                  />
                )}
              </div>

              <Separator />

              {/* Referral Details */}
              <div className="grid grid-cols-2 gap-4">
                {/* Referral Type */}
                <div className="space-y-2">
                  <Label>Referral Type</Label>
                  <RadioGroup
                    value={referralType}
                    onValueChange={(v: "consultation" | "transfer" | "co-management") => setReferralType(v)}
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="consultation" id="consultation" />
                      <Label htmlFor="consultation" className="font-normal">
                        Consultation
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="transfer" id="transfer" />
                      <Label htmlFor="transfer" className="font-normal">
                        Transfer of Care
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="co-management" id="co-management" />
                      <Label htmlFor="co-management" className="font-normal">
                        Co-Management
                      </Label>
                    </div>
                  </RadioGroup>
                </div>

                {/* Priority */}
                <div className="space-y-2">
                  <Label>Priority</Label>
                  <RadioGroup
                    value={priority}
                    onValueChange={(v: "routine" | "urgent" | "emergent") => setPriority(v)}
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="routine" id="routine" />
                      <Label htmlFor="routine" className="font-normal flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-gray-400" />
                        Routine (2-4 weeks)
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="urgent" id="urgent" />
                      <Label htmlFor="urgent" className="font-normal flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-amber-500" />
                        Urgent (1-2 weeks)
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="emergent" id="emergent" />
                      <Label htmlFor="emergent" className="font-normal flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-red-500" />
                        Emergent (24-48 hrs)
                      </Label>
                    </div>
                  </RadioGroup>
                </div>
              </div>

              <Separator />

              {/* Reason for Referral */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Reason for Referral
                </Label>
                <ReasonSelector
                  specialty={selectedSpecialty}
                  value={reasonForReferral}
                  onChange={setReasonForReferral}
                />
              </div>

              <Separator />

              {/* Clinical Summary */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Clinical Summary
                  </Label>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleGenerateSummary}
                    disabled={isGeneratingAI}
                  >
                    {isGeneratingAI ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Wand2 className="h-4 w-4 mr-1" />
                        AI Generate
                      </>
                    )}
                  </Button>
                </div>
                <Textarea
                  value={clinicalSummary}
                  onChange={(e) => setClinicalSummary(e.target.value)}
                  placeholder="Enter clinical summary or use AI to generate..."
                  className="min-h-[150px]"
                />

                {/* Include Options */}
                <div className="flex items-center gap-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="include-labs"
                      checked={includeLabResults}
                      onCheckedChange={(c) => setIncludeLabResults(!!c)}
                    />
                    <Label htmlFor="include-labs" className="text-sm font-normal">
                      Include recent lab results
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="include-meds"
                      checked={includeMedications}
                      onCheckedChange={(c) => setIncludeMedications(!!c)}
                    />
                    <Label htmlFor="include-meds" className="text-sm font-normal">
                      Include medication list
                    </Label>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Patient Preferences */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Patient Preferences (Optional)
                </Label>
                <Textarea
                  value={patientPreferences}
                  onChange={(e) => setPatientPreferences(e.target.value)}
                  placeholder="E.g., prefers afternoon appointments, needs wheelchair accessibility..."
                  className="min-h-[80px]"
                />
              </div>

              <Separator />

              {/* Document Attachments */}
              <DocumentAttachment
                documents={documents}
                onAdd={(doc) => setDocuments([...documents, doc])}
                onRemove={(docId) => setDocuments(documents.filter((d) => d.id !== docId))}
              />

              <Separator />

              {/* Insurance Authorization */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Insurance Authorization
                </Label>
                <AuthorizationCheck
                  requiresAuth={patientInsurance?.requiresAuth || false}
                  status={authStatus}
                  onCheck={handleCheckAuth}
                />
              </div>
            </div>
          </ScrollArea>

          {/* Summary Sidebar */}
          <div className="w-72 border-l bg-muted/30 p-4">
            <ReferralSummary
              specialist={selectedSpecialist}
              referralType={referralType}
              priority={priority}
              reason={reasonForReferral}
              documents={documents}
            />

            {/* Patient Insurance */}
            {patientInsurance && (
              <Card className="mt-4">
                <CardHeader className="py-3 px-4">
                  <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                    <CreditCard className="h-3 w-3" />
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

            {/* Recent Diagnoses */}
            {recentDiagnoses.length > 0 && (
              <Card className="mt-4">
                <CardHeader className="py-3 px-4">
                  <CardTitle className="text-xs font-medium text-muted-foreground">
                    Recent Diagnoses
                  </CardTitle>
                </CardHeader>
                <CardContent className="py-0 px-4 pb-3 space-y-1">
                  {recentDiagnoses.slice(0, 3).map((dx, i) => (
                    <div key={i} className="text-xs">
                      <span className="font-mono text-primary">{dx.code}</span>
                      <span className="text-muted-foreground ml-1">
                        {dx.description}
                      </span>
                    </div>
                  ))}
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
            <DialogTitle>Send Referral</DialogTitle>
            <DialogDescription>
              Please confirm the referral details before sending.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {selectedSpecialist && (
              <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="font-medium">{selectedSpecialist.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {selectedSpecialist.specialty}
                  </p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground ml-auto" />
              </div>
            )}

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Referral Type</span>
                <span className="capitalize">{referralType}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Priority</span>
                <Badge
                  variant={
                    priority === "emergent"
                      ? "destructive"
                      : priority === "urgent"
                      ? "default"
                      : "secondary"
                  }
                >
                  {priority}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Attachments</span>
                <span>{documents.length} document(s)</span>
              </div>
            </div>

            {!isInNetwork && (
              <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <span className="text-sm text-amber-800">
                  This specialist is out of network. Higher costs may apply.
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
                  Sending...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Send Referral
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
// Compact Referral Widget
// ============================================================================

interface ReferralWidgetProps {
  patientId: string;
  recentReferrals?: Referral[];
  onNewReferral: () => void;
  onViewReferral: (referralId: string) => void;
}

export function ReferralWidget({
  patientId,
  recentReferrals = [],
  onNewReferral,
  onViewReferral,
}: ReferralWidgetProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Send className="h-4 w-4" />
            Referrals
          </CardTitle>
          <Button size="sm" onClick={onNewReferral}>
            <Plus className="h-4 w-4 mr-1" />
            New Referral
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {recentReferrals.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground">
            <Send className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No recent referrals</p>
          </div>
        ) : (
          <div className="space-y-2">
            {recentReferrals.slice(0, 3).map((referral) => (
              <div
                key={referral.id}
                className="flex items-center justify-between p-2 bg-muted/30 rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => referral.id && onViewReferral(referral.id)}
              >
                <div>
                  <p className="text-sm font-medium">
                    {referral.specialist?.name || "Unknown Specialist"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {referral.specialist?.specialty}
                  </p>
                </div>
                <Badge
                  variant={
                    referral.status === "completed"
                      ? "default"
                      : referral.status === "scheduled"
                      ? "secondary"
                      : "outline"
                  }
                >
                  {referral.status}
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
// Referral Form Skeleton
// ============================================================================

export function ReferralFormSkeleton() {
  return (
    <div className="animate-pulse space-y-4 p-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-6 w-40 bg-muted rounded" />
          <div className="h-4 w-32 bg-muted rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-9 w-20 bg-muted rounded" />
          <div className="h-9 w-32 bg-muted rounded" />
        </div>
      </div>

      <div className="h-px bg-muted" />

      <div className="space-y-3">
        <div className="h-4 w-24 bg-muted rounded" />
        <div className="h-10 w-full bg-muted rounded" />
      </div>

      <div className="space-y-3">
        <div className="h-4 w-20 bg-muted rounded" />
        <div className="h-10 w-full bg-muted rounded" />
      </div>

      <div className="h-px bg-muted" />

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="h-4 w-24 bg-muted rounded" />
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-6 w-32 bg-muted rounded" />
            ))}
          </div>
        </div>
        <div className="space-y-2">
          <div className="h-4 w-16 bg-muted rounded" />
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-6 w-36 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>

      <div className="h-px bg-muted" />

      <div className="space-y-3">
        <div className="h-4 w-36 bg-muted rounded" />
        <div className="h-32 w-full bg-muted rounded" />
      </div>
    </div>
  );
}

export default ReferralForm;
