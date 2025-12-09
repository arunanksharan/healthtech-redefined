"use client";

// SOAP Note Editor Component
// EPIC-UX-007: Clinical Workflows Interface - Journey 7.3 Clinical Documentation

import React, { useState, useCallback, useRef, useEffect } from "react";
import { format } from "date-fns";
import {
  Mic,
  MicOff,
  Wand2,
  FileText,
  Clock,
  Save,
  Lock,
  Unlock,
  ChevronDown,
  ChevronRight,
  Copy,
  History,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  X,
  Plus,
  Loader2,
  MessageSquare,
  ListChecks,
  Stethoscope,
  Brain,
  ClipboardList,
  Settings2,
  RotateCcw,
  User,
  Calendar,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
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
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  useClinicalWorkflowsStore,
  type ClinicalNote,
  type SubjectiveSection,
  type ObjectiveSection,
  type AssessmentSection,
  type PlanSection,
} from "@/lib/store/clinical-workflows-store";

// ============================================================================
// Types
// ============================================================================

interface SOAPNoteEditorProps {
  patientId: string;
  patientName: string;
  encounterId?: string;
  encounterDate?: string;
  previousNote?: ClinicalNote;
  onSave: (note: ClinicalNote) => void;
  onSign: (note: ClinicalNote) => void;
  onCancel: () => void;
}

interface SOAPSection {
  id: "subjective" | "objective" | "assessment" | "plan";
  title: string;
  icon: React.ReactNode;
  description: string;
  color: string;
}

interface NoteTemplate {
  id: string;
  name: string;
  category: string;
  subjective: Partial<SubjectiveSection>;
  objective: Partial<ObjectiveSection>;
  assessment: Partial<AssessmentSection>;
  plan: Partial<PlanSection>;
}

interface AISuggestion {
  id: string;
  section: "subjective" | "objective" | "assessment" | "plan";
  field: string;
  suggestion: string;
  confidence: number;
  source: string;
}

// ============================================================================
// Constants
// ============================================================================

const SOAP_SECTIONS: SOAPSection[] = [
  {
    id: "subjective",
    title: "Subjective",
    icon: <MessageSquare className="h-4 w-4" />,
    description: "Patient's reported symptoms, history, and concerns",
    color: "bg-blue-500",
  },
  {
    id: "objective",
    title: "Objective",
    icon: <Stethoscope className="h-4 w-4" />,
    description: "Physical exam findings, vital signs, and test results",
    color: "bg-green-500",
  },
  {
    id: "assessment",
    title: "Assessment",
    icon: <Brain className="h-4 w-4" />,
    description: "Clinical diagnosis and medical decision making",
    color: "bg-purple-500",
  },
  {
    id: "plan",
    title: "Plan",
    icon: <ClipboardList className="h-4 w-4" />,
    description: "Treatment plan, orders, and follow-up",
    color: "bg-orange-500",
  },
];

const NOTE_TEMPLATES: NoteTemplate[] = [
  {
    id: "template-wellness",
    name: "Annual Wellness Visit",
    category: "Preventive",
    subjective: {
      chiefComplaint: "Annual wellness examination",
      hpiNarrative: "Patient presents for routine annual wellness visit. No acute complaints.",
    },
    objective: {
      generalAppearance: "Well-appearing, in no acute distress",
      examFindings: {},
    },
    assessment: {
      primaryDiagnosis: {
        code: "Z00.00",
        description: "Encounter for general adult medical examination without abnormal findings",
        status: "active",
      },
    },
    plan: {
      planNarrative: "Continue current medications. Routine labs ordered. Return in 1 year for annual exam.",
    },
  },
  {
    id: "template-htn-fu",
    name: "Hypertension Follow-up",
    category: "Chronic Care",
    subjective: {
      chiefComplaint: "Hypertension follow-up",
      hpiNarrative: "Patient presents for blood pressure management follow-up. Patient reports compliance with medication regimen.",
    },
    objective: {
      generalAppearance: "Well-appearing, in no acute distress",
    },
    assessment: {
      primaryDiagnosis: {
        code: "I10",
        description: "Essential (primary) hypertension",
        status: "active",
      },
    },
    plan: {
      planNarrative: "Continue current antihypertensive regimen. Home BP monitoring encouraged. Return in 3 months.",
    },
  },
  {
    id: "template-dm-fu",
    name: "Diabetes Follow-up",
    category: "Chronic Care",
    subjective: {
      chiefComplaint: "Diabetes mellitus follow-up",
      hpiNarrative: "Patient presents for diabetes management. Reports good adherence to diet and medications. No hypoglycemic episodes.",
    },
    objective: {
      generalAppearance: "Well-appearing, in no acute distress",
    },
    assessment: {
      primaryDiagnosis: {
        code: "E11.9",
        description: "Type 2 diabetes mellitus without complications",
        status: "active",
      },
    },
    plan: {
      planNarrative: "Continue current diabetes regimen. HbA1c ordered. Foot exam performed. Return in 3 months.",
    },
  },
  {
    id: "template-uri",
    name: "Upper Respiratory Infection",
    category: "Acute",
    subjective: {
      chiefComplaint: "Cold symptoms",
      hpiNarrative: "Patient reports onset of symptoms approximately 3-5 days ago with nasal congestion, sore throat, and mild cough. No fever, shortness of breath, or chest pain.",
    },
    objective: {
      generalAppearance: "Mildly ill-appearing but in no acute distress",
    },
    assessment: {
      primaryDiagnosis: {
        code: "J06.9",
        description: "Acute upper respiratory infection, unspecified",
        status: "active",
      },
    },
    plan: {
      planNarrative: "Supportive care with rest, hydration, and OTC symptomatic treatment. Return if symptoms worsen or persist beyond 10 days.",
    },
  },
];

// ============================================================================
// Sub-Components
// ============================================================================

// Voice Dictation Button
interface VoiceDictationButtonProps {
  isRecording: boolean;
  onStartRecording: () => void;
  onStopRecording: () => void;
  disabled?: boolean;
}

function VoiceDictationButton({
  isRecording,
  onStartRecording,
  onStopRecording,
  disabled,
}: VoiceDictationButtonProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant={isRecording ? "destructive" : "outline"}
            size="icon"
            onClick={isRecording ? onStopRecording : onStartRecording}
            disabled={disabled}
            className={cn(
              "relative",
              isRecording && "animate-pulse"
            )}
          >
            {isRecording ? (
              <MicOff className="h-4 w-4" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
            {isRecording && (
              <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-500 animate-ping" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          {isRecording ? "Stop dictation" : "Start voice dictation"}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// AI Suggestion Card
interface AISuggestionCardProps {
  suggestion: AISuggestion;
  onAccept: () => void;
  onReject: () => void;
}

function AISuggestionCard({ suggestion, onAccept, onReject }: AISuggestionCardProps) {
  return (
    <div className="flex items-start gap-3 p-3 bg-purple-50 border border-purple-200 rounded-lg">
      <Sparkles className="h-4 w-4 text-purple-600 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-medium text-purple-700">AI Suggestion</span>
          <Badge variant="secondary" className="text-xs">
            {Math.round(suggestion.confidence * 100)}% confidence
          </Badge>
        </div>
        <p className="text-sm text-purple-900">{suggestion.suggestion}</p>
        <p className="text-xs text-purple-600 mt-1">Source: {suggestion.source}</p>
      </div>
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-green-600 hover:text-green-700 hover:bg-green-100"
          onClick={onAccept}
        >
          <CheckCircle2 className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-red-600 hover:text-red-700 hover:bg-red-100"
          onClick={onReject}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// Section Editor
interface SectionEditorProps {
  section: SOAPSection;
  value: string;
  onChange: (value: string) => void;
  isRecording: boolean;
  onStartRecording: () => void;
  onStopRecording: () => void;
  suggestions: AISuggestion[];
  onAcceptSuggestion: (suggestion: AISuggestion) => void;
  onRejectSuggestion: (suggestionId: string) => void;
  onAIAssist: () => void;
  isLocked: boolean;
  placeholder?: string;
}

function SectionEditor({
  section,
  value,
  onChange,
  isRecording,
  onStartRecording,
  onStopRecording,
  suggestions,
  onAcceptSuggestion,
  onRejectSuggestion,
  onAIAssist,
  isLocked,
  placeholder,
}: SectionEditorProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.max(120, textarea.scrollHeight)}px`;
    }
  }, [value]);

  const sectionSuggestions = suggestions.filter((s) => s.section === section.id);

  return (
    <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
      <div className="border rounded-lg overflow-hidden">
        <CollapsibleTrigger asChild>
          <div
            className={cn(
              "flex items-center justify-between p-3 cursor-pointer hover:bg-muted/50 transition-colors",
              isExpanded && "border-b"
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn("w-1 h-8 rounded-full", section.color)} />
              <div className="flex items-center gap-2">
                {section.icon}
                <span className="font-medium">{section.title}</span>
              </div>
              {value && (
                <Badge variant="secondary" className="text-xs">
                  {value.split(/\s+/).length} words
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              {sectionSuggestions.length > 0 && (
                <Badge variant="default" className="text-xs bg-purple-600">
                  <Sparkles className="h-3 w-3 mr-1" />
                  {sectionSuggestions.length} suggestion{sectionSuggestions.length !== 1 ? "s" : ""}
                </Badge>
              )}
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </div>
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="p-4 space-y-3">
            <p className="text-xs text-muted-foreground">{section.description}</p>

            {/* AI Suggestions */}
            {sectionSuggestions.length > 0 && (
              <div className="space-y-2">
                {sectionSuggestions.map((suggestion) => (
                  <AISuggestionCard
                    key={suggestion.id}
                    suggestion={suggestion}
                    onAccept={() => onAcceptSuggestion(suggestion)}
                    onReject={() => onRejectSuggestion(suggestion.id)}
                  />
                ))}
              </div>
            )}

            {/* Text Editor */}
            <div className="relative">
              <Textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder || `Enter ${section.title.toLowerCase()} information...`}
                disabled={isLocked}
                className={cn(
                  "min-h-[120px] resize-none pr-24",
                  isLocked && "opacity-60"
                )}
              />
              <div className="absolute top-2 right-2 flex items-center gap-1">
                <VoiceDictationButton
                  isRecording={isRecording}
                  onStartRecording={onStartRecording}
                  onStopRecording={onStopRecording}
                  disabled={isLocked}
                />
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={onAIAssist}
                        disabled={isLocked}
                      >
                        <Wand2 className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>AI Assist</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

// Previous Notes Panel
interface PreviousNotesPanelProps {
  notes: ClinicalNote[];
  onCopySection: (section: string, content: string) => void;
}

function PreviousNotesPanel({ notes, onCopySection }: PreviousNotesPanelProps) {
  const [selectedNote, setSelectedNote] = useState<ClinicalNote | null>(
    notes[0] || null
  );

  if (notes.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No previous notes available</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <Select
        value={selectedNote?.id || ""}
        onValueChange={(value) => {
          const note = notes.find((n) => n.id === value);
          setSelectedNote(note || null);
        }}
      >
        <SelectTrigger>
          <SelectValue placeholder="Select a previous note" />
        </SelectTrigger>
        <SelectContent>
          {notes.map((note) => (
            <SelectItem key={note.id} value={note.id || ""}>
              <div className="flex items-center gap-2">
                <Calendar className="h-3 w-3" />
                {format(new Date(note.createdAt || Date.now()), "MMM d, yyyy")} -{" "}
                {note.noteType}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {selectedNote && (
        <ScrollArea className="h-[400px]">
          <div className="space-y-4">
            {/* Subjective */}
            {selectedNote.subjective?.hpiNarrative && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-xs text-blue-700">Subjective</Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs"
                    onClick={() =>
                      onCopySection("subjective", selectedNote.subjective?.hpiNarrative || "")
                    }
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    Copy
                  </Button>
                </div>
                <p className="text-sm">{selectedNote.subjective.hpiNarrative}</p>
              </div>
            )}

            {/* Objective */}
            {selectedNote.objective?.generalAppearance && (
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-xs text-green-700">Objective</Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs"
                    onClick={() =>
                      onCopySection("objective", selectedNote.objective?.generalAppearance || "")
                    }
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    Copy
                  </Button>
                </div>
                <p className="text-sm">{selectedNote.objective.generalAppearance}</p>
              </div>
            )}

            {/* Assessment */}
            {selectedNote.assessment?.assessmentNarrative && (
              <div className="p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-xs text-purple-700">Assessment</Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs"
                    onClick={() =>
                      onCopySection(
                        "assessment",
                        selectedNote.assessment?.assessmentNarrative || ""
                      )
                    }
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    Copy
                  </Button>
                </div>
                <p className="text-sm">{selectedNote.assessment.assessmentNarrative}</p>
              </div>
            )}

            {/* Plan */}
            {selectedNote.plan?.planNarrative && (
              <div className="p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-xs text-orange-700">Plan</Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs"
                    onClick={() =>
                      onCopySection("plan", selectedNote.plan?.planNarrative || "")
                    }
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    Copy
                  </Button>
                </div>
                <p className="text-sm">{selectedNote.plan.planNarrative}</p>
              </div>
            )}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

// Template Selector
interface TemplateSelectorProps {
  onSelectTemplate: (template: NoteTemplate) => void;
}

function TemplateSelector({ onSelectTemplate }: TemplateSelectorProps) {
  const groupedTemplates = NOTE_TEMPLATES.reduce((acc, template) => {
    if (!acc[template.category]) acc[template.category] = [];
    acc[template.category].push(template);
    return acc;
  }, {} as Record<string, NoteTemplate[]>);

  return (
    <div className="space-y-4">
      {Object.entries(groupedTemplates).map(([category, templates]) => (
        <div key={category}>
          <Label className="text-xs text-muted-foreground mb-2 block">
            {category}
          </Label>
          <div className="grid grid-cols-2 gap-2">
            {templates.map((template) => (
              <Button
                key={template.id}
                variant="outline"
                className="justify-start h-auto p-3"
                onClick={() => onSelectTemplate(template)}
              >
                <FileText className="h-4 w-4 mr-2 shrink-0" />
                <span className="text-left text-sm">{template.name}</span>
              </Button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// Note Progress Indicator
interface NoteProgressProps {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}

function NoteProgress({ subjective, objective, assessment, plan }: NoteProgressProps) {
  const sections = [
    { name: "S", value: subjective, color: "bg-blue-500" },
    { name: "O", value: objective, color: "bg-green-500" },
    { name: "A", value: assessment, color: "bg-purple-500" },
    { name: "P", value: plan, color: "bg-orange-500" },
  ];

  const completedCount = sections.filter((s) => s.value.trim().length > 0).length;
  const progress = (completedCount / 4) * 100;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Completion</span>
        <span className="font-medium">{completedCount}/4 sections</span>
      </div>
      <Progress value={progress} className="h-2" />
      <div className="flex items-center justify-between">
        {sections.map((section) => (
          <div
            key={section.name}
            className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-colors",
              section.value.trim().length > 0
                ? cn(section.color, "text-white")
                : "bg-muted text-muted-foreground"
            )}
          >
            {section.name}
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function SOAPNoteEditor({
  patientId,
  patientName,
  encounterId,
  encounterDate,
  previousNote,
  onSave,
  onSign,
  onCancel,
}: SOAPNoteEditorProps) {
  // Content state
  const [subjective, setSubjective] = useState(previousNote?.subjective?.hpiNarrative || "");
  const [objective, setObjective] = useState(previousNote?.objective?.generalAppearance || "");
  const [assessment, setAssessment] = useState(previousNote?.assessment?.assessmentNarrative || "");
  const [plan, setPlan] = useState(previousNote?.plan?.planNarrative || "");

  // UI state
  const [activeSection, setActiveSection] = useState<"subjective" | "objective" | "assessment" | "plan" | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isLocked, setIsLocked] = useState(previousNote?.status === "signed");
  const [isSaving, setIsSaving] = useState(false);
  const [showSignDialog, setShowSignDialog] = useState(false);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<AISuggestion[]>([]);
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // Speech recognition ref
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Store
  const { clinicalNotes, generateSOAPFromVoice } = useClinicalWorkflowsStore();

  // Get previous notes for this patient
  const previousNotes = clinicalNotes.filter((n) => n.patientId === patientId);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== "undefined" && "webkitSpeechRecognition" in window) {
      const SpeechRecognition = window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = "en-US";

      recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = Array.from(event.results)
          .map((result) => result[0].transcript)
          .join("");

        if (activeSection) {
          const setter = {
            subjective: setSubjective,
            objective: setObjective,
            assessment: setAssessment,
            plan: setPlan,
          }[activeSection];

          if (setter) {
            setter((prev) => prev + " " + transcript);
          }
        }
      };

      recognitionRef.current.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error("Speech recognition error:", event.error);
        setIsRecording(false);
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [activeSection]);

  // Handlers
  const handleStartRecording = useCallback((section: "subjective" | "objective" | "assessment" | "plan") => {
    if (recognitionRef.current) {
      setActiveSection(section);
      setIsRecording(true);
      recognitionRef.current.start();
    }
  }, []);

  const handleStopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
      setActiveSection(null);
    }
  }, []);

  const handleAIAssist = useCallback(
    async (section: "subjective" | "objective" | "assessment" | "plan") => {
      setIsGeneratingAI(true);

      // Simulate AI generation
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const mockSuggestions: Record<string, AISuggestion> = {
        subjective: {
          id: `suggestion-${Date.now()}`,
          section: "subjective",
          field: "hpiNarrative",
          suggestion:
            "Based on the patient's chief complaint and history, consider adding: Duration and onset of symptoms, aggravating/alleviating factors, and associated symptoms.",
          confidence: 0.85,
          source: "Clinical guidelines",
        },
        objective: {
          id: `suggestion-${Date.now()}`,
          section: "objective",
          field: "examFindings",
          suggestion:
            "Consider documenting: Vital signs interpretation, relevant system-specific exam findings, and pertinent negative findings.",
          confidence: 0.82,
          source: "Physical exam best practices",
        },
        assessment: {
          id: `suggestion-${Date.now()}`,
          section: "assessment",
          field: "assessmentNarrative",
          suggestion:
            "Based on the subjective and objective findings, the clinical picture is consistent with [condition]. Differential diagnoses to consider include [alternatives].",
          confidence: 0.78,
          source: "Diagnostic reasoning",
        },
        plan: {
          id: `suggestion-${Date.now()}`,
          section: "plan",
          field: "planNarrative",
          suggestion:
            "Recommended plan elements: 1) Diagnostic workup, 2) Treatment approach, 3) Patient education, 4) Follow-up timeline, 5) Red flags to return sooner.",
          confidence: 0.88,
          source: "Treatment guidelines",
        },
      };

      setAiSuggestions((prev) => [...prev, mockSuggestions[section]]);
      setIsGeneratingAI(false);
    },
    []
  );

  const handleAcceptSuggestion = useCallback((suggestion: AISuggestion) => {
    const setter = {
      subjective: setSubjective,
      objective: setObjective,
      assessment: setAssessment,
      plan: setPlan,
    }[suggestion.section];

    if (setter) {
      setter((prev) => (prev ? prev + "\n\n" + suggestion.suggestion : suggestion.suggestion));
    }

    setAiSuggestions((prev) => prev.filter((s) => s.id !== suggestion.id));
  }, []);

  const handleRejectSuggestion = useCallback((suggestionId: string) => {
    setAiSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
  }, []);

  const handleApplyTemplate = useCallback((template: NoteTemplate) => {
    if (template.subjective?.hpiNarrative) {
      setSubjective(template.subjective.hpiNarrative);
    }
    if (template.objective?.generalAppearance) {
      setObjective(template.objective.generalAppearance);
    }
    if (template.assessment?.primaryDiagnosis) {
      const pd = template.assessment.primaryDiagnosis;
      const diagnosisText = typeof pd === 'string'
        ? pd
        : `${pd.code} - ${pd.description}`;
      setAssessment(`Primary Diagnosis: ${diagnosisText}`);
    }
    if (template.plan?.planNarrative) {
      setPlan(template.plan.planNarrative);
    }
    setShowTemplateDialog(false);
  }, []);

  const handleCopyFromPrevious = useCallback(
    (section: string, content: string) => {
      const setter = {
        subjective: setSubjective,
        objective: setObjective,
        assessment: setAssessment,
        plan: setPlan,
      }[section];

      if (setter) {
        setter(content);
      }
    },
    []
  );

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      const note: ClinicalNote = {
        id: previousNote?.id || `note-${Date.now()}`,
        patientId,
        encounterId,
        authorId: "current-provider-id",
        noteType: "soap",
        subjective: {
          chiefComplaint: "",
          hpiNarrative: subjective,
        },
        objective: {
          generalAppearance: objective,
          examFindings: {},
        },
        assessment: {
          assessmentNarrative: assessment,
        },
        plan: {
          planNarrative: plan,
        },
        status: "draft",
        createdAt: previousNote?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      onSave(note);
      setLastSaved(new Date());
    } finally {
      setIsSaving(false);
    }
  }, [patientId, encounterId, subjective, objective, assessment, plan, previousNote, onSave]);

  const handleSign = useCallback(async () => {
    const note: ClinicalNote = {
      id: previousNote?.id || `note-${Date.now()}`,
      patientId,
      encounterId,
      authorId: "current-provider-id",
      noteType: "soap",
      subjective: {
        chiefComplaint: "",
        hpiNarrative: subjective,
      },
      objective: {
        generalAppearance: objective,
        examFindings: {},
      },
      assessment: {
        assessmentNarrative: assessment,
      },
      plan: {
        planNarrative: plan,
      },
      status: "signed",
      signedAt: new Date().toISOString(),
      signedBy: "current-provider-id",
      createdAt: previousNote?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    onSign(note);
    setIsLocked(true);
    setShowSignDialog(false);
  }, [patientId, encounterId, subjective, objective, assessment, plan, previousNote, onSign]);

  const canSign = subjective.trim() && objective.trim() && assessment.trim() && plan.trim();

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            SOAP Note
            {isLocked && (
              <Badge variant="secondary" className="ml-2">
                <Lock className="h-3 w-3 mr-1" />
                Signed
              </Badge>
            )}
          </h2>
          <p className="text-sm text-muted-foreground">
            Patient: <span className="font-medium">{patientName}</span>
            {encounterDate && (
              <span className="ml-2">
                Date: {format(new Date(encounterDate), "MMM d, yyyy")}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {lastSaved && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-green-600" />
              Saved {format(lastSaved, "h:mm a")}
            </span>
          )}
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant="outline"
            onClick={handleSave}
            disabled={isLocked || isSaving}
          >
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Draft
              </>
            )}
          </Button>
          <Button
            onClick={() => setShowSignDialog(true)}
            disabled={!canSign || isLocked}
          >
            <Lock className="mr-2 h-4 w-4" />
            Sign & Lock
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <div className="flex h-full">
          {/* Main Editor */}
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4 max-w-3xl">
              {/* Quick Actions */}
              <div className="flex items-center gap-2 mb-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowTemplateDialog(true)}
                  disabled={isLocked}
                >
                  <FileText className="h-4 w-4 mr-1" />
                  Use Template
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSubjective("");
                    setObjective("");
                    setAssessment("");
                    setPlan("");
                  }}
                  disabled={isLocked}
                >
                  <RotateCcw className="h-4 w-4 mr-1" />
                  Clear All
                </Button>
                {isGeneratingAI && (
                  <Badge variant="secondary" className="ml-auto">
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    AI generating...
                  </Badge>
                )}
              </div>

              {/* SOAP Sections */}
              {SOAP_SECTIONS.map((section) => {
                const value = {
                  subjective,
                  objective,
                  assessment,
                  plan,
                }[section.id];

                const setter = {
                  subjective: setSubjective,
                  objective: setObjective,
                  assessment: setAssessment,
                  plan: setPlan,
                }[section.id];

                return (
                  <SectionEditor
                    key={section.id}
                    section={section}
                    value={value}
                    onChange={setter}
                    isRecording={isRecording && activeSection === section.id}
                    onStartRecording={() => handleStartRecording(section.id)}
                    onStopRecording={handleStopRecording}
                    suggestions={aiSuggestions}
                    onAcceptSuggestion={handleAcceptSuggestion}
                    onRejectSuggestion={handleRejectSuggestion}
                    onAIAssist={() => handleAIAssist(section.id)}
                    isLocked={isLocked}
                  />
                );
              })}
            </div>
          </ScrollArea>

          {/* Sidebar */}
          <div className="w-80 border-l bg-muted/30">
            <Tabs defaultValue="progress" className="h-full flex flex-col">
              <TabsList className="w-full justify-start rounded-none border-b bg-transparent p-0">
                <TabsTrigger
                  value="progress"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary"
                >
                  Progress
                </TabsTrigger>
                <TabsTrigger
                  value="previous"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary"
                >
                  Previous
                </TabsTrigger>
                <TabsTrigger
                  value="templates"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary"
                >
                  Templates
                </TabsTrigger>
              </TabsList>

              <TabsContent value="progress" className="flex-1 p-4 m-0">
                <NoteProgress
                  subjective={subjective}
                  objective={objective}
                  assessment={assessment}
                  plan={plan}
                />

                <Separator className="my-4" />

                <div className="space-y-3">
                  <Label className="text-xs text-muted-foreground">Note Info</Label>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Status</span>
                      <Badge variant={isLocked ? "default" : "secondary"}>
                        {isLocked ? "Signed" : "Draft"}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Word Count</span>
                      <span>
                        {(subjective + objective + assessment + plan)
                          .split(/\s+/)
                          .filter(Boolean).length}
                      </span>
                    </div>
                    {lastSaved && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Last Saved</span>
                        <span>{format(lastSaved, "h:mm a")}</span>
                      </div>
                    )}
                  </div>
                </div>

                <Separator className="my-4" />

                <div className="space-y-3">
                  <Label className="text-xs text-muted-foreground">Quick Tips</Label>
                  <div className="space-y-2 text-xs text-muted-foreground">
                    <p className="flex items-start gap-2">
                      <Mic className="h-3 w-3 mt-0.5 shrink-0" />
                      Use voice dictation for hands-free documentation
                    </p>
                    <p className="flex items-start gap-2">
                      <Wand2 className="h-3 w-3 mt-0.5 shrink-0" />
                      AI Assist suggests content based on context
                    </p>
                    <p className="flex items-start gap-2">
                      <Copy className="h-3 w-3 mt-0.5 shrink-0" />
                      Copy sections from previous notes
                    </p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="previous" className="flex-1 p-4 m-0 overflow-auto">
                <PreviousNotesPanel
                  notes={previousNotes}
                  onCopySection={handleCopyFromPrevious}
                />
              </TabsContent>

              <TabsContent value="templates" className="flex-1 p-4 m-0 overflow-auto">
                <TemplateSelector onSelectTemplate={handleApplyTemplate} />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>

      {/* Template Selection Dialog */}
      <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Select Note Template</DialogTitle>
            <DialogDescription>
              Choose a template to pre-fill the SOAP note sections
            </DialogDescription>
          </DialogHeader>
          <TemplateSelector onSelectTemplate={handleApplyTemplate} />
        </DialogContent>
      </Dialog>

      {/* Sign Confirmation Dialog */}
      <Dialog open={showSignDialog} onOpenChange={setShowSignDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Sign & Lock Note</DialogTitle>
            <DialogDescription>
              Once signed, this note cannot be edited. Please review before signing.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-800">
                  This action is irreversible
                </p>
                <p className="text-xs text-amber-700 mt-1">
                  The note will be locked and timestamped with your electronic signature.
                </p>
              </div>
            </div>

            <NoteProgress
              subjective={subjective}
              objective={objective}
              assessment={assessment}
              plan={plan}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSignDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSign}>
              <Lock className="mr-2 h-4 w-4" />
              Sign & Lock Note
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ============================================================================
// Compact SOAP Note Widget
// ============================================================================

interface SOAPNoteWidgetProps {
  patientId: string;
  recentNotes?: ClinicalNote[];
  onNewNote: () => void;
  onViewNote: (noteId: string) => void;
}

export function SOAPNoteWidget({
  patientId,
  recentNotes = [],
  onNewNote,
  onViewNote,
}: SOAPNoteWidgetProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Clinical Notes
          </CardTitle>
          <Button size="sm" onClick={onNewNote}>
            <Plus className="h-4 w-4 mr-1" />
            New Note
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {recentNotes.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground">
            <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No clinical notes</p>
          </div>
        ) : (
          <div className="space-y-2">
            {recentNotes.slice(0, 3).map((note) => (
              <div
                key={note.id}
                className="flex items-center justify-between p-2 bg-muted/30 rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => note.id && onViewNote(note.id)}
              >
                <div>
                  <p className="text-sm font-medium capitalize">
                    {note.noteType} Note
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {format(new Date(note.createdAt || Date.now()), "MMM d, yyyy")}
                  </p>
                </div>
                <Badge
                  variant={note.status === "signed" ? "default" : "secondary"}
                >
                  {note.status === "signed" ? (
                    <Lock className="h-3 w-3 mr-1" />
                  ) : (
                    <Unlock className="h-3 w-3 mr-1" />
                  )}
                  {note.status}
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
// SOAP Note Skeleton
// ============================================================================

export function SOAPNoteEditorSkeleton() {
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
          <div className="h-9 w-32 bg-muted rounded" />
        </div>
      </div>

      <div className="h-px bg-muted" />

      <div className="flex gap-2">
        <div className="h-8 w-28 bg-muted rounded" />
        <div className="h-8 w-24 bg-muted rounded" />
      </div>

      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="border rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-1 h-8 bg-muted rounded-full" />
            <div className="h-5 w-24 bg-muted rounded" />
          </div>
          <div className="h-32 bg-muted rounded" />
        </div>
      ))}
    </div>
  );
}

export default SOAPNoteEditor;
