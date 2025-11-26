"use client";

// Specialist Consultation Request Components
// EPIC-UX-010: Provider Collaboration Hub - Journey 10.2

import React, { useEffect, useState } from "react";
import { format } from "date-fns";
import {
  Stethoscope, Clock, Check, X, AlertCircle, Paperclip, User, ChevronRight,
  Send, MessageSquare, FileText, Loader2, Calendar, Building2, Flag,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  useCollaborationStore,
  type ConsultationRequest,
  type ConsultPriority,
  type ConsultType,
  type ConsultStatus,
  type PatientContext,
  type User as UserType,
} from "@/lib/store/collaboration-store";

// Specialty options
const SPECIALTIES = [
  "Cardiology",
  "Endocrinology",
  "Nephrology",
  "Neurology",
  "Oncology",
  "Pulmonology",
  "Gastroenterology",
  "Rheumatology",
  "Infectious Disease",
  "Psychiatry",
];

// Status badge
function ConsultStatusBadge({ status }: { status: ConsultStatus }) {
  const config = {
    pending: { label: "Pending", className: "bg-amber-100 text-amber-700", icon: Clock },
    accepted: { label: "Accepted", className: "bg-blue-100 text-blue-700", icon: Check },
    in_progress: { label: "In Progress", className: "bg-purple-100 text-purple-700", icon: Stethoscope },
    completed: { label: "Completed", className: "bg-green-100 text-green-700", icon: Check },
    declined: { label: "Declined", className: "bg-red-100 text-red-700", icon: X },
  };
  const c = config[status];
  return (
    <Badge variant="secondary" className={cn("flex items-center gap-1", c.className)}>
      <c.icon className="h-3 w-3" />
      {c.label}
    </Badge>
  );
}

// Priority badge
function PriorityBadge({ priority }: { priority: ConsultPriority }) {
  const config = {
    routine: { label: "Routine", className: "bg-gray-100 text-gray-700" },
    urgent: { label: "Urgent", className: "bg-amber-100 text-amber-700" },
    emergent: { label: "Emergent", className: "bg-red-100 text-red-700" },
  };
  const c = config[priority];
  return <Badge variant="secondary" className={c.className}>{c.label}</Badge>;
}

// Consultation request form
interface ConsultationFormProps {
  patient: PatientContext;
  onSubmit: (data: Partial<ConsultationRequest>) => Promise<void>;
  onCancel: () => void;
}

export function ConsultationForm({ patient, onSubmit, onCancel }: ConsultationFormProps) {
  const [specialty, setSpecialty] = useState("");
  const [priority, setPriority] = useState<ConsultPriority>("routine");
  const [consultType, setConsultType] = useState<ConsultType>("opinion");
  const [reason, setReason] = useState("");
  const [clinicalQuestion, setClinicalQuestion] = useState("");
  const [attachments, setAttachments] = useState<string[]>(["Recent A1C results", "Current medication list"]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    await onSubmit({
      specialty,
      priority,
      consultType,
      reason,
      clinicalQuestion,
      patient,
      attachments: attachments.map((name, i) => ({
        id: `att-${i}`,
        name,
        type: "application/pdf",
        size: 100000,
        url: `/files/${name.toLowerCase().replace(/\s/g, "-")}.pdf`,
        uploadedAt: new Date().toISOString(),
      })),
    });
    setIsSubmitting(false);
  };

  return (
    <div className="space-y-6">
      {/* Patient info */}
      <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
        <Avatar>
          <AvatarFallback><User className="h-5 w-5" /></AvatarFallback>
        </Avatar>
        <div>
          <p className="font-medium">{patient.name}</p>
          <p className="text-sm text-muted-foreground">MRN: {patient.mrn} | {patient.age}y {patient.gender} | Room {patient.room}</p>
        </div>
      </div>

      {/* Consultation type section */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-sm">CONSULTATION TYPE</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Specialty</Label>
            <Select value={specialty} onValueChange={setSpecialty}>
              <SelectTrigger><SelectValue placeholder="Select specialty..." /></SelectTrigger>
              <SelectContent>
                {SPECIALTIES.map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Priority</Label>
            <RadioGroup value={priority} onValueChange={(v) => setPriority(v as ConsultPriority)} className="flex gap-4">
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="routine" id="routine" />
                <Label htmlFor="routine" className="cursor-pointer">Routine</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="urgent" id="urgent" />
                <Label htmlFor="urgent" className="cursor-pointer text-amber-600">Urgent</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="emergent" id="emergent" />
                <Label htmlFor="emergent" className="cursor-pointer text-red-600">Emergent</Label>
              </div>
            </RadioGroup>
          </div>

          <div className="space-y-2">
            <Label>Consult Type</Label>
            <RadioGroup value={consultType} onValueChange={(v) => setConsultType(v as ConsultType)} className="flex gap-4">
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="opinion" id="opinion" />
                <Label htmlFor="opinion" className="cursor-pointer">Opinion only</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="co_management" id="co_management" />
                <Label htmlFor="co_management" className="cursor-pointer">Co-management</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="transfer" id="transfer" />
                <Label htmlFor="transfer" className="cursor-pointer">Transfer</Label>
              </div>
            </RadioGroup>
          </div>
        </CardContent>
      </Card>

      {/* Reason for consultation */}
      <div className="space-y-2">
        <Label>Reason for Consultation</Label>
        <Textarea
          placeholder="Describe the reason for this consultation..."
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={4}
        />
      </div>

      {/* Clinical question */}
      <div className="space-y-2">
        <Label>Clinical Question</Label>
        <Textarea
          placeholder="What specific question would you like answered?"
          value={clinicalQuestion}
          onChange={(e) => setClinicalQuestion(e.target.value)}
          rows={2}
        />
      </div>

      {/* Attachments */}
      <div className="space-y-2">
        <Label>Attach Relevant Documents</Label>
        <div className="space-y-2">
          {["Recent A1C results", "Current medication list", "Last 3 clinical notes"].map((doc) => (
            <div key={doc} className="flex items-center space-x-2">
              <Checkbox
                id={doc}
                checked={attachments.includes(doc)}
                onCheckedChange={(checked) =>
                  setAttachments(checked ? [...attachments, doc] : attachments.filter((a) => a !== doc))
                }
              />
              <Label htmlFor={doc} className="cursor-pointer">{doc}</Label>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="outline" onClick={onCancel} className="flex-1">Cancel</Button>
        <Button onClick={handleSubmit} disabled={!specialty || !reason || isSubmitting} className="flex-1">
          {isSubmitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
          Submit Consult
        </Button>
      </div>
    </div>
  );
}

// Consultation card for list view
interface ConsultationCardProps {
  consultation: ConsultationRequest;
  onClick: () => void;
  onAccept?: () => void;
}

export function ConsultationCard({ consultation, onClick, onAccept }: ConsultationCardProps) {
  const timeAgo = format(new Date(consultation.createdAt), "MMM d, h:mm a");

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Building2 className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{consultation.specialty}</span>
              <PriorityBadge priority={consultation.priority} />
              <ConsultStatusBadge status={consultation.status} />
            </div>
            <p className="text-sm text-muted-foreground">
              From: {consultation.requesterName} ({consultation.requesterDepartment})
            </p>
            <div className="flex items-center gap-2 mt-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">{consultation.patient.name}</span>
              <span className="text-xs text-muted-foreground">MRN: {consultation.patient.mrn}</span>
            </div>
            <p className="text-sm mt-2 line-clamp-2">{consultation.reason}</p>
            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              <span><Clock className="h-3 w-3 inline mr-1" />{timeAgo}</span>
              {consultation.attachments.length > 0 && (
                <span><Paperclip className="h-3 w-3 inline mr-1" />{consultation.attachments.length} files</span>
              )}
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );
}

// Consultation detail view
interface ConsultationDetailProps {
  consultation: ConsultationRequest;
  onClose: () => void;
  onAccept: () => void;
  onDecline: (reason: string) => void;
  onRespond: (response: string, recommendations: string[]) => void;
  isCurrentUserConsultant: boolean;
}

export function ConsultationDetail({
  consultation,
  onClose,
  onAccept,
  onDecline,
  onRespond,
  isCurrentUserConsultant,
}: ConsultationDetailProps) {
  const [response, setResponse] = useState("");
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [newRec, setNewRec] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const addRecommendation = () => {
    if (newRec.trim()) {
      setRecommendations([...recommendations, newRec.trim()]);
      setNewRec("");
    }
  };

  const handleRespond = async () => {
    setIsSubmitting(true);
    await onRespond(response, recommendations);
    setIsSubmitting(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Stethoscope className="h-5 w-5" />
          Consultation Request
        </h2>
        <Button variant="ghost" size="icon" onClick={onClose}><X className="h-4 w-4" /></Button>
      </div>

      {/* Status and priority */}
      <div className="flex items-center gap-2">
        <ConsultStatusBadge status={consultation.status} />
        <PriorityBadge priority={consultation.priority} />
        <Badge variant="outline">{consultation.consultType.replace("_", "-")}</Badge>
      </div>

      {/* Patient info */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <Avatar>
              <AvatarFallback><User className="h-5 w-5" /></AvatarFallback>
            </Avatar>
            <div>
              <p className="font-medium">{consultation.patient.name}</p>
              <p className="text-sm text-muted-foreground">
                MRN: {consultation.patient.mrn} | {consultation.patient.age}y {consultation.patient.gender} | Room {consultation.patient.room}
              </p>
              {consultation.patient.primaryDiagnosis && (
                <Badge variant="outline" className="mt-1">{consultation.patient.primaryDiagnosis}</Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Request details */}
      <div className="space-y-4">
        <div>
          <Label className="text-xs text-muted-foreground">FROM</Label>
          <p className="text-sm">{consultation.requesterName} - {consultation.requesterDepartment}</p>
        </div>
        <div>
          <Label className="text-xs text-muted-foreground">SPECIALTY REQUESTED</Label>
          <p className="text-sm">{consultation.specialty}</p>
        </div>
        <div>
          <Label className="text-xs text-muted-foreground">REASON FOR CONSULTATION</Label>
          <p className="text-sm">{consultation.reason}</p>
        </div>
        <div>
          <Label className="text-xs text-muted-foreground">CLINICAL QUESTION</Label>
          <p className="text-sm font-medium">{consultation.clinicalQuestion}</p>
        </div>
      </div>

      {/* Attachments */}
      {consultation.attachments.length > 0 && (
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">ATTACHMENTS</Label>
          <div className="space-y-1">
            {consultation.attachments.map((att) => (
              <div key={att.id} className="flex items-center gap-2 p-2 bg-muted/50 rounded text-sm">
                <FileText className="h-4 w-4" />
                <span>{att.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Response section */}
      {consultation.response && (
        <Card className="border-green-200 bg-green-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-green-800">CONSULTANT RESPONSE</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm">{consultation.response.text}</p>
            {consultation.response.recommendations.length > 0 && (
              <div>
                <Label className="text-xs text-muted-foreground">RECOMMENDATIONS</Label>
                <ul className="list-disc list-inside text-sm space-y-1 mt-1">
                  {consultation.response.recommendations.map((rec, i) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              Responded: {format(new Date(consultation.response.respondedAt), "MMM d, yyyy h:mm a")}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Actions for consultant */}
      {isCurrentUserConsultant && consultation.status === "pending" && (
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => onDecline("Unable to accept at this time")} className="flex-1">
            Decline
          </Button>
          <Button onClick={onAccept} className="flex-1">Accept Consultation</Button>
        </div>
      )}

      {/* Response form for consultant */}
      {isCurrentUserConsultant && consultation.status === "in_progress" && (
        <div className="space-y-4 border-t pt-4">
          <h3 className="font-medium">Submit Response</h3>
          <div className="space-y-2">
            <Label>Response</Label>
            <Textarea
              placeholder="Enter your consultation response..."
              value={response}
              onChange={(e) => setResponse(e.target.value)}
              rows={4}
            />
          </div>
          <div className="space-y-2">
            <Label>Recommendations</Label>
            <div className="flex gap-2">
              <Input
                placeholder="Add a recommendation..."
                value={newRec}
                onChange={(e) => setNewRec(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addRecommendation())}
              />
              <Button variant="outline" onClick={addRecommendation}>Add</Button>
            </div>
            {recommendations.length > 0 && (
              <ul className="space-y-1">
                {recommendations.map((rec, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm p-2 bg-muted/50 rounded">
                    <Check className="h-4 w-4 text-green-600" />
                    {rec}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-5 w-5 ml-auto"
                      onClick={() => setRecommendations(recommendations.filter((_, j) => j !== i))}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <Button onClick={handleRespond} disabled={!response || isSubmitting} className="w-full">
            {isSubmitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
            Submit Response
          </Button>
        </div>
      )}
    </div>
  );
}

// New consultation dialog
interface NewConsultationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patient: PatientContext;
}

export function NewConsultationDialog({ open, onOpenChange, patient }: NewConsultationDialogProps) {
  const { createConsultation } = useCollaborationStore();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>New Consultation Request</DialogTitle>
        </DialogHeader>
        <ConsultationForm
          patient={patient}
          onSubmit={async (data) => {
            await createConsultation(data);
            onOpenChange(false);
          }}
          onCancel={() => onOpenChange(false)}
        />
      </DialogContent>
    </Dialog>
  );
}

// Main Consultations Dashboard
export function ConsultationsDashboard() {
  const [selectedConsultation, setSelectedConsultation] = useState<ConsultationRequest | null>(null);
  const [filter, setFilter] = useState<"all" | "pending" | "mine">("all");

  const {
    consultations,
    currentUser,
    isLoadingConsultations,
    fetchConsultations,
    acceptConsultation,
    respondToConsultation,
    declineConsultation,
  } = useCollaborationStore();

  useEffect(() => { fetchConsultations(); }, [fetchConsultations]);

  const filteredConsultations = consultations.filter((c) => {
    if (filter === "pending") return c.status === "pending";
    if (filter === "mine") return c.consultantId === currentUser?.id || c.requesterId === currentUser?.id;
    return true;
  });

  if (selectedConsultation) {
    const isConsultant = selectedConsultation.specialty === currentUser?.specialty;
    return (
      <div className="max-w-2xl mx-auto">
        <ConsultationDetail
          consultation={selectedConsultation}
          onClose={() => setSelectedConsultation(null)}
          onAccept={() => acceptConsultation(selectedConsultation.id)}
          onDecline={(reason) => declineConsultation(selectedConsultation.id, reason)}
          onRespond={(response, recs) => respondToConsultation(selectedConsultation.id, response, recs)}
          isCurrentUserConsultant={isConsultant}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Stethoscope className="h-6 w-6" />Consultations
        </h1>
        <div className="flex gap-2">
          <Select value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
            <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="mine">My Consults</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoadingConsultations ? (
        <div className="text-center py-8"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></div>
      ) : filteredConsultations.length === 0 ? (
        <Card><CardContent className="py-8 text-center text-muted-foreground">No consultations found</CardContent></Card>
      ) : (
        <div className="space-y-3">
          {filteredConsultations.map((consultation) => (
            <ConsultationCard
              key={consultation.id}
              consultation={consultation}
              onClick={() => setSelectedConsultation(consultation)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Consultations widget for dashboard
export function ConsultationsWidget() {
  const { consultations, fetchConsultations } = useCollaborationStore();

  useEffect(() => { fetchConsultations(); }, [fetchConsultations]);

  const pendingCount = consultations.filter((c) => c.status === "pending").length;
  const recentConsultations = consultations.slice(0, 3);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Stethoscope className="h-4 w-4" />Consultations
          </CardTitle>
          {pendingCount > 0 && <Badge variant="destructive">{pendingCount} pending</Badge>}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {recentConsultations.map((c) => (
          <div key={c.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{c.specialty}</span>
                <ConsultStatusBadge status={c.status} />
              </div>
              <p className="text-xs text-muted-foreground truncate">{c.patient.name} - {c.reason.slice(0, 50)}...</p>
            </div>
          </div>
        ))}
        <Button variant="ghost" className="w-full text-xs">View All Consultations</Button>
      </CardContent>
    </Card>
  );
}

export default ConsultationsDashboard;
