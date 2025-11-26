"use client";

// Mobile Patient Chart - Simplified Chart View for Providers
// EPIC-UX-012: Mobile Applications - Journey 12.5

import React, { useState, useEffect } from "react";
import { format, differenceInYears } from "date-fns";
import {
  ChevronLeft, ChevronRight, User, AlertTriangle, Heart, Pill, FileText,
  Activity, Calendar, MessageSquare, Phone, MoreVertical, Clock,
  Stethoscope, TestTube, Clipboard, Shield, Edit, Plus, Check,
  ChevronDown, ChevronUp, Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useMobileStore, type QuickPatient } from "@/lib/store/mobile-store";

// Patient header banner
interface PatientBannerProps {
  patient: {
    id: string;
    name: string;
    mrn: string;
    dob: string;
    gender: string;
    allergies: string[];
    photoUrl?: string;
  };
  onBack: () => void;
  onAction: (action: string) => void;
}

function PatientBanner({ patient, onBack, onAction }: PatientBannerProps) {
  const age = differenceInYears(new Date(), new Date(patient.dob));

  return (
    <div className="sticky top-0 z-10 bg-background border-b">
      <div className="flex items-center gap-2 p-3">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ChevronLeft className="h-5 w-5" />
        </Button>
        <Avatar className="h-10 w-10">
          <AvatarImage src={patient.photoUrl} />
          <AvatarFallback>{patient.name.split(" ").map(n => n[0]).join("")}</AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <p className="font-semibold truncate">{patient.name}</p>
          <p className="text-xs text-muted-foreground">
            {age}y {patient.gender} • MRN: {patient.mrn}
          </p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onAction("call")}>
              <Phone className="h-4 w-4 mr-2" /> Call Patient
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onAction("message")}>
              <MessageSquare className="h-4 w-4 mr-2" /> Send Message
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onAction("schedule")}>
              <Calendar className="h-4 w-4 mr-2" /> Schedule Visit
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Allergy Alert */}
      {patient.allergies.length > 0 && (
        <div className="px-4 pb-3">
          <div className="flex items-center gap-2 p-2 bg-red-50 rounded-lg border border-red-200">
            <AlertTriangle className="h-4 w-4 text-red-600 shrink-0" />
            <span className="text-xs text-red-700 font-medium">Allergies:</span>
            <span className="text-xs text-red-600 truncate">{patient.allergies.join(", ")}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// Vital signs card
interface VitalsCardProps {
  vitals: {
    bp: string;
    hr: string;
    temp: string;
    spo2: string;
    weight: string;
    recordedAt: string;
  };
}

function VitalsCard({ vitals }: VitalsCardProps) {
  const vitalItems = [
    { label: "BP", value: vitals.bp, unit: "mmHg", icon: Activity },
    { label: "HR", value: vitals.hr, unit: "bpm", icon: Heart },
    { label: "Temp", value: vitals.temp, unit: "°F", icon: Activity },
    { label: "SpO2", value: vitals.spo2, unit: "%", icon: Activity },
    { label: "Wt", value: vitals.weight, unit: "lbs", icon: Activity },
  ];

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Latest Vitals</CardTitle>
          <span className="text-xs text-muted-foreground">{vitals.recordedAt}</span>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="w-full">
          <div className="flex gap-3">
            {vitalItems.map((vital, i) => (
              <div key={i} className="p-2 bg-muted/50 rounded-lg min-w-[70px] text-center">
                <p className="text-xs text-muted-foreground">{vital.label}</p>
                <p className="text-sm font-semibold">{vital.value}</p>
                <p className="text-[10px] text-muted-foreground">{vital.unit}</p>
              </div>
            ))}
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// Problem list section
interface ProblemListProps {
  problems: Array<{
    id: string;
    name: string;
    icd10: string;
    status: "active" | "resolved" | "chronic";
    onsetDate: string;
  }>;
}

function ProblemList({ problems }: ProblemListProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const activeProblems = problems.filter(p => p.status === "active" || p.status === "chronic");

  const statusColor = {
    active: "bg-amber-100 text-amber-700",
    chronic: "bg-blue-100 text-blue-700",
    resolved: "bg-green-100 text-green-700",
  };

  return (
    <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardHeader className="pb-2 cursor-pointer hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Clipboard className="h-4 w-4" />
                Problem List ({activeProblems.length} active)
              </CardTitle>
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="space-y-2">
              {activeProblems.map((problem) => (
                <div key={problem.id} className="flex items-center justify-between p-2 bg-muted/30 rounded">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{problem.name}</p>
                    <p className="text-xs text-muted-foreground">{problem.icd10}</p>
                  </div>
                  <Badge variant="secondary" className={cn("text-xs shrink-0", statusColor[problem.status])}>
                    {problem.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

// Medications section
interface MedicationsListProps {
  medications: Array<{
    id: string;
    name: string;
    dosage: string;
    frequency: string;
    prescriber: string;
  }>;
}

function MedicationsList({ medications }: MedicationsListProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardHeader className="pb-2 cursor-pointer hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Pill className="h-4 w-4" />
                Medications ({medications.length})
              </CardTitle>
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="space-y-2">
              {medications.map((med) => (
                <div key={med.id} className="p-2 bg-muted/30 rounded">
                  <p className="text-sm font-medium">{med.name}</p>
                  <p className="text-xs text-muted-foreground">{med.dosage} • {med.frequency}</p>
                </div>
              ))}
            </div>
            <Button variant="ghost" size="sm" className="w-full mt-2">
              <Plus className="h-4 w-4 mr-1" /> Add Medication
            </Button>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

// Recent labs section
interface RecentLabsProps {
  labs: Array<{
    id: string;
    name: string;
    value: string;
    unit: string;
    status: "normal" | "abnormal" | "critical";
    date: string;
  }>;
}

function RecentLabs({ labs }: RecentLabsProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const statusConfig = {
    normal: { color: "text-green-600", bg: "bg-green-50" },
    abnormal: { color: "text-amber-600", bg: "bg-amber-50" },
    critical: { color: "text-red-600", bg: "bg-red-50" },
  };

  return (
    <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardHeader className="pb-2 cursor-pointer hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <TestTube className="h-4 w-4" />
                Recent Labs
              </CardTitle>
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="space-y-2">
              {labs.map((lab) => (
                <div
                  key={lab.id}
                  className={cn("p-2 rounded flex items-center justify-between", statusConfig[lab.status].bg)}
                >
                  <div>
                    <p className="text-sm font-medium">{lab.name}</p>
                    <p className="text-xs text-muted-foreground">{lab.date}</p>
                  </div>
                  <div className="text-right">
                    <p className={cn("text-sm font-semibold", statusConfig[lab.status].color)}>
                      {lab.value} {lab.unit}
                    </p>
                    <Badge variant="outline" className={cn("text-[10px]", statusConfig[lab.status].color)}>
                      {lab.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="ghost" size="sm" className="w-full mt-2">
              View All Labs <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

// Visit history
interface VisitHistoryProps {
  visits: Array<{
    id: string;
    date: string;
    type: string;
    provider: string;
    chiefComplaint: string;
  }>;
}

function VisitHistory({ visits }: VisitHistoryProps) {
  return (
    <div className="space-y-3">
      {visits.map((visit) => (
        <Card key={visit.id}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs">{visit.type}</Badge>
                  <span className="text-xs text-muted-foreground">{visit.date}</span>
                </div>
                <p className="text-sm font-medium mt-1 truncate">{visit.chiefComplaint}</p>
                <p className="text-xs text-muted-foreground">{visit.provider}</p>
              </div>
              <Button variant="ghost" size="sm">
                <FileText className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Quick note input
function QuickNoteInput({ onSave }: { onSave: (note: string) => void }) {
  const [note, setNote] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    if (!note.trim()) return;
    setIsSaving(true);
    await new Promise(r => setTimeout(r, 500));
    onSave(note);
    setNote("");
    setIsSaving(false);
  };

  return (
    <Card>
      <CardContent className="p-3">
        <textarea
          className="w-full min-h-[80px] p-2 text-sm border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder="Add a quick note..."
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        <div className="flex justify-end mt-2">
          <Button size="sm" onClick={handleSave} disabled={!note.trim() || isSaving}>
            {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Check className="h-4 w-4 mr-1" /> Save Note</>}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Main Mobile Patient Chart Component
export function MobilePatientChart({ patientId, onBack }: { patientId: string; onBack: () => void }) {
  const [activeTab, setActiveTab] = useState("summary");
  const [isLoading, setIsLoading] = useState(true);

  // Mock patient data
  const patient = {
    id: patientId,
    name: "John Doe",
    mrn: "12345",
    dob: "1965-03-15",
    gender: "M",
    allergies: ["Penicillin", "Sulfa"],
  };

  const vitals = {
    bp: "128/82",
    hr: "72",
    temp: "98.6",
    spo2: "98",
    weight: "185",
    recordedAt: "Today 9:30 AM",
  };

  const problems = [
    { id: "p1", name: "Type 2 Diabetes Mellitus", icd10: "E11.9", status: "chronic" as const, onsetDate: "2019-01-15" },
    { id: "p2", name: "Essential Hypertension", icd10: "I10", status: "active" as const, onsetDate: "2018-06-20" },
    { id: "p3", name: "Hyperlipidemia", icd10: "E78.5", status: "active" as const, onsetDate: "2020-03-10" },
  ];

  const medications = [
    { id: "m1", name: "Metformin 1000mg", dosage: "1 tablet", frequency: "Twice daily", prescriber: "Dr. Sharma" },
    { id: "m2", name: "Lisinopril 10mg", dosage: "1 tablet", frequency: "Once daily", prescriber: "Dr. Sharma" },
    { id: "m3", name: "Atorvastatin 20mg", dosage: "1 tablet", frequency: "At bedtime", prescriber: "Dr. Patel" },
  ];

  const labs = [
    { id: "l1", name: "HbA1c", value: "7.2", unit: "%", status: "abnormal" as const, date: "Nov 20, 2024" },
    { id: "l2", name: "eGFR", value: "85", unit: "mL/min", status: "normal" as const, date: "Nov 20, 2024" },
    { id: "l3", name: "Potassium", value: "4.5", unit: "mEq/L", status: "normal" as const, date: "Nov 20, 2024" },
    { id: "l4", name: "LDL Cholesterol", value: "125", unit: "mg/dL", status: "abnormal" as const, date: "Nov 15, 2024" },
  ];

  const visits = [
    { id: "v1", date: "Nov 20, 2024", type: "Follow-up", provider: "Dr. Priya Sharma", chiefComplaint: "Diabetes management, medication review" },
    { id: "v2", date: "Oct 15, 2024", type: "Telehealth", provider: "Dr. Priya Sharma", chiefComplaint: "BP check, refills needed" },
    { id: "v3", date: "Sep 5, 2024", type: "Annual Physical", provider: "Dr. Priya Sharma", chiefComplaint: "Annual wellness exam" },
  ];

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      <PatientBanner
        patient={patient}
        onBack={onBack}
        onAction={(action) => console.log("Action:", action)}
      />

      <div className="p-4 space-y-4">
        {/* Quick Actions */}
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex-1">
            <Edit className="h-4 w-4 mr-1" /> New Note
          </Button>
          <Button variant="outline" size="sm" className="flex-1">
            <Pill className="h-4 w-4 mr-1" /> Order Rx
          </Button>
          <Button variant="outline" size="sm" className="flex-1">
            <TestTube className="h-4 w-4 mr-1" /> Order Lab
          </Button>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="summary" className="text-xs">Summary</TabsTrigger>
            <TabsTrigger value="notes" className="text-xs">Notes</TabsTrigger>
            <TabsTrigger value="orders" className="text-xs">Orders</TabsTrigger>
            <TabsTrigger value="history" className="text-xs">History</TabsTrigger>
          </TabsList>

          <TabsContent value="summary" className="mt-4 space-y-4">
            <VitalsCard vitals={vitals} />
            <ProblemList problems={problems} />
            <MedicationsList medications={medications} />
            <RecentLabs labs={labs} />
          </TabsContent>

          <TabsContent value="notes" className="mt-4 space-y-4">
            <QuickNoteInput onSave={(note) => console.log("Saving note:", note)} />
            <VisitHistory visits={visits} />
          </TabsContent>

          <TabsContent value="orders" className="mt-4">
            <Card>
              <CardContent className="py-8 text-center">
                <Clipboard className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">No pending orders</p>
                <div className="flex gap-2 justify-center mt-4">
                  <Button size="sm"><Pill className="h-4 w-4 mr-1" /> New Rx</Button>
                  <Button size="sm" variant="outline"><TestTube className="h-4 w-4 mr-1" /> Order Lab</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="mt-4">
            <VisitHistory visits={visits} />
          </TabsContent>
        </Tabs>
      </div>

      {/* Bottom Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-background border-t p-3">
        <div className="flex gap-2">
          <Button className="flex-1">
            <Stethoscope className="h-4 w-4 mr-2" /> Start Encounter
          </Button>
        </div>
      </div>
    </div>
  );
}

// Compact chart summary widget
export function PatientChartWidget({ patient }: { patient: QuickPatient }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Avatar className="h-8 w-8">
          <AvatarFallback className="text-xs">{patient.name.split(" ").map(n => n[0]).join("")}</AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{patient.name}</p>
          <p className="text-xs text-muted-foreground">{patient.age}y {patient.gender} • MRN: {patient.mrn}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-1">
        {patient.conditions.slice(0, 2).map((c, i) => (
          <Badge key={i} variant="secondary" className="text-[10px]">{c}</Badge>
        ))}
      </div>
    </div>
  );
}

export default MobilePatientChart;
