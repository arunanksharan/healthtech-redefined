"use client";

// SBAR Shift Handoff Components
// EPIC-UX-010: Provider Collaboration Hub - Journey 10.3

import React, { useEffect, useState } from "react";
import { format } from "date-fns";
import {
  ArrowRight, Clock, Check, X, AlertTriangle, Edit, ChevronDown, ChevronUp,
  User, Bed, FileText, Loader2, Plus, Save, Send, CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  useCollaborationStore,
  type SBARHandoff,
  type SBARPatient,
  type HandoffStatus,
  type User as UserType,
} from "@/lib/store/collaboration-store";

// Status badge
function HandoffStatusBadge({ status }: { status: HandoffStatus }) {
  const config = {
    draft: { label: "Draft", className: "bg-gray-100 text-gray-700", icon: Edit },
    pending_acknowledgment: { label: "Pending", className: "bg-amber-100 text-amber-700", icon: Clock },
    acknowledged: { label: "Acknowledged", className: "bg-blue-100 text-blue-700", icon: Check },
    completed: { label: "Completed", className: "bg-green-100 text-green-700", icon: CheckCircle2 },
  };
  const c = config[status];
  return (
    <Badge variant="secondary" className={cn("flex items-center gap-1", c.className)}>
      <c.icon className="h-3 w-3" />
      {c.label}
    </Badge>
  );
}

// SBAR Patient Form
interface SBARPatientFormProps {
  patient: SBARPatient;
  onChange: (updated: SBARPatient) => void;
  onRemove: () => void;
}

function SBARPatientForm({ patient, onChange, onRemove }: SBARPatientFormProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [newTask, setNewTask] = useState("");
  const [newAlert, setNewAlert] = useState("");

  const updateField = (field: keyof SBARPatient, value: string) => {
    onChange({ ...patient, [field]: value });
  };

  const addTask = () => {
    if (newTask.trim()) {
      onChange({
        ...patient,
        tasks: [...patient.tasks, { task: newTask.trim(), priority: "medium", completed: false }],
      });
      setNewTask("");
    }
  };

  const addAlert = () => {
    if (newAlert.trim()) {
      onChange({ ...patient, alerts: [...patient.alerts, newAlert.trim()] });
      setNewAlert("");
    }
  };

  return (
    <Card>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bed className="h-5 w-5 text-muted-foreground" />
                <div>
                  <CardTitle className="text-sm">Room {patient.room} - {patient.patientName}</CardTitle>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {patient.alerts.length > 0 && (
                  <Badge variant="destructive" className="text-xs">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    {patient.alerts.length} alerts
                  </Badge>
                )}
                {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </div>
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="space-y-4 pt-0">
            {/* Situation */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold text-blue-700">S - SITUATION</Label>
              <Textarea
                placeholder="Current patient situation..."
                value={patient.situation}
                onChange={(e) => updateField("situation", e.target.value)}
                rows={2}
                className="text-sm"
              />
            </div>

            {/* Background */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold text-green-700">B - BACKGROUND</Label>
              <Textarea
                placeholder="Relevant history and background..."
                value={patient.background}
                onChange={(e) => updateField("background", e.target.value)}
                rows={2}
                className="text-sm"
              />
            </div>

            {/* Assessment */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold text-amber-700">A - ASSESSMENT</Label>
              <Textarea
                placeholder="Current assessment and status..."
                value={patient.assessment}
                onChange={(e) => updateField("assessment", e.target.value)}
                rows={2}
                className="text-sm"
              />
            </div>

            {/* Recommendation */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold text-purple-700">R - RECOMMENDATION</Label>
              <Textarea
                placeholder="Recommended actions and plan..."
                value={patient.recommendation}
                onChange={(e) => updateField("recommendation", e.target.value)}
                rows={2}
                className="text-sm"
              />
            </div>

            {/* Alerts */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold text-red-700">ALERTS</Label>
              <div className="flex flex-wrap gap-2">
                {patient.alerts.map((alert, i) => (
                  <Badge key={i} variant="destructive" className="flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    {alert}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-4 w-4 ml-1 hover:bg-red-700"
                      onClick={() => onChange({ ...patient, alerts: patient.alerts.filter((_, j) => j !== i) })}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Add alert..."
                  value={newAlert}
                  onChange={(e) => setNewAlert(e.target.value)}
                  className="flex-1 text-sm"
                />
                <Button variant="outline" size="sm" onClick={addAlert}>Add</Button>
              </div>
            </div>

            {/* Tasks */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold">PENDING TASKS</Label>
              <div className="space-y-1">
                {patient.tasks.map((task, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 bg-muted/50 rounded text-sm">
                    <Checkbox
                      checked={task.completed}
                      onCheckedChange={(checked) => {
                        const updated = [...patient.tasks];
                        updated[i] = { ...task, completed: !!checked };
                        onChange({ ...patient, tasks: updated });
                      }}
                    />
                    <span className={cn(task.completed && "line-through text-muted-foreground")}>{task.task}</span>
                    <Badge variant="outline" className="ml-auto text-xs">{task.priority}</Badge>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Add task..."
                  value={newTask}
                  onChange={(e) => setNewTask(e.target.value)}
                  className="flex-1 text-sm"
                />
                <Button variant="outline" size="sm" onClick={addTask}>Add</Button>
              </div>
            </div>

            <Button variant="ghost" size="sm" className="text-red-600" onClick={onRemove}>
              <X className="h-4 w-4 mr-1" />Remove Patient
            </Button>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

// SBAR Patient View (read-only)
interface SBARPatientViewProps {
  patient: SBARPatient;
  defaultOpen?: boolean;
}

function SBARPatientView({ patient, defaultOpen = false }: SBARPatientViewProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Card>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/50 pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bed className="h-5 w-5 text-muted-foreground" />
                <div>
                  <CardTitle className="text-sm">Room {patient.room} - {patient.patientName}</CardTitle>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {patient.alerts.length > 0 && (
                  <Badge variant="destructive" className="text-xs">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    {patient.alerts.length}
                  </Badge>
                )}
                {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </div>
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="space-y-3 pt-0">
            <div>
              <p className="text-xs font-semibold text-blue-700 mb-1">S - SITUATION</p>
              <p className="text-sm">{patient.situation}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-green-700 mb-1">B - BACKGROUND</p>
              <p className="text-sm">{patient.background}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-amber-700 mb-1">A - ASSESSMENT</p>
              <p className="text-sm">{patient.assessment}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-purple-700 mb-1">R - RECOMMENDATION</p>
              <p className="text-sm">{patient.recommendation}</p>
            </div>
            {patient.alerts.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {patient.alerts.map((alert, i) => (
                  <Badge key={i} variant="destructive">
                    <AlertTriangle className="h-3 w-3 mr-1" />{alert}
                  </Badge>
                ))}
              </div>
            )}
            {patient.tasks.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-semibold">Tasks ({patient.tasks.filter((t) => !t.completed).length} pending)</p>
                {patient.tasks.map((task, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    {task.completed ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <div className="h-4 w-4 border rounded" />
                    )}
                    <span className={cn(task.completed && "line-through text-muted-foreground")}>{task.task}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

// Create Handoff Form
interface CreateHandoffFormProps {
  onSubmit: (handoff: Partial<SBARHandoff>) => Promise<void>;
  onCancel: () => void;
}

export function CreateHandoffForm({ onSubmit, onCancel }: CreateHandoffFormProps) {
  const { onlineUsers, currentUser } = useCollaborationStore();
  const [toUserId, setToUserId] = useState("");
  const [ward, setWard] = useState("Cardiology Unit A");
  const [shiftType, setShiftType] = useState<"night_to_day" | "day_to_night">("night_to_day");
  const [patients, setPatients] = useState<SBARPatient[]>([
    {
      id: "sp-new-1",
      patientId: "p1",
      patientName: "",
      room: "",
      situation: "",
      background: "",
      assessment: "",
      recommendation: "",
      alerts: [],
      tasks: [],
    },
  ]);
  const [reviewed, setReviewed] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const availableUsers = onlineUsers.filter((u) => u.id !== currentUser?.id && u.role.includes("Nurse"));

  const addPatient = () => {
    setPatients([
      ...patients,
      {
        id: `sp-new-${Date.now()}`,
        patientId: "",
        patientName: "",
        room: "",
        situation: "",
        background: "",
        assessment: "",
        recommendation: "",
        alerts: [],
        tasks: [],
      },
    ]);
  };

  const updatePatient = (index: number, updated: SBARPatient) => {
    const newPatients = [...patients];
    newPatients[index] = updated;
    setPatients(newPatients);
  };

  const removePatient = (index: number) => {
    setPatients(patients.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    const toUser = onlineUsers.find((u) => u.id === toUserId);
    setIsSubmitting(true);
    await onSubmit({
      toUserId,
      toUserName: toUser?.name || "",
      ward,
      shiftType,
      patients: patients.filter((p) => p.patientName),
    });
    setIsSubmitting(false);
  };

  return (
    <div className="space-y-6">
      {/* Header info */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>From</Label>
              <div className="flex items-center gap-2 p-2 bg-muted/50 rounded">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>{currentUser?.name.split(" ").map((n) => n[0]).join("")}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="text-sm font-medium">{currentUser?.name}</p>
                  <p className="text-xs text-muted-foreground">{shiftType === "night_to_day" ? "Night Shift" : "Day Shift"}</p>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label>To</Label>
              <Select value={toUserId} onValueChange={setToUserId}>
                <SelectTrigger><SelectValue placeholder="Select recipient..." /></SelectTrigger>
                <SelectContent>
                  {availableUsers.map((u) => (
                    <SelectItem key={u.id} value={u.id}>{u.name} ({u.role})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Ward</Label>
              <Input value={ward} onChange={(e) => setWard(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Shift Type</Label>
              <Select value={shiftType} onValueChange={(v) => setShiftType(v as typeof shiftType)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="night_to_day">Night to Day</SelectItem>
                  <SelectItem value="day_to_night">Day to Night</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Patients */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Patients to Hand Off ({patients.length})</h3>
          <Button variant="outline" size="sm" onClick={addPatient}>
            <Plus className="h-4 w-4 mr-1" />Add Patient
          </Button>
        </div>
        {patients.map((patient, i) => (
          <SBARPatientForm
            key={patient.id}
            patient={patient}
            onChange={(updated) => updatePatient(i, updated)}
            onRemove={() => removePatient(i)}
          />
        ))}
      </div>

      {/* Review checkbox */}
      <div className="flex items-center space-x-2 p-3 bg-muted/50 rounded-lg">
        <Checkbox id="reviewed" checked={reviewed} onCheckedChange={(c) => setReviewed(!!c)} />
        <Label htmlFor="reviewed" className="cursor-pointer">I have reviewed all patient handoffs</Label>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="outline" onClick={onCancel}><X className="h-4 w-4 mr-1" />Cancel</Button>
        <Button variant="outline"><Save className="h-4 w-4 mr-1" />Save Draft</Button>
        <Button
          onClick={handleSubmit}
          disabled={!toUserId || !reviewed || patients.filter((p) => p.patientName).length === 0 || isSubmitting}
          className="flex-1"
        >
          {isSubmitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
          Complete Handoff
        </Button>
      </div>
    </div>
  );
}

// Handoff Card (list view)
interface HandoffCardProps {
  handoff: SBARHandoff;
  onClick: () => void;
  onAcknowledge?: () => void;
}

export function HandoffCard({ handoff, onClick, onAcknowledge }: HandoffCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-medium">{handoff.ward}</span>
              <Badge variant="outline">{handoff.shiftType.replace("_", " ")}</Badge>
              <HandoffStatusBadge status={handoff.status} />
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Avatar className="h-6 w-6">
                <AvatarFallback className="text-xs">{handoff.fromUserName.split(" ").map((n) => n[0]).join("")}</AvatarFallback>
              </Avatar>
              <span>{handoff.fromUserName}</span>
              <ArrowRight className="h-4 w-4" />
              <Avatar className="h-6 w-6">
                <AvatarFallback className="text-xs">{handoff.toUserName.split(" ").map((n) => n[0]).join("")}</AvatarFallback>
              </Avatar>
              <span>{handoff.toUserName}</span>
            </div>
            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              <span><User className="h-3 w-3 inline mr-1" />{handoff.patients.length} patients</span>
              <span><Clock className="h-3 w-3 inline mr-1" />{format(new Date(handoff.createdAt), "MMM d, h:mm a")}</span>
            </div>
          </div>
          {handoff.status === "pending_acknowledgment" && onAcknowledge && (
            <Button size="sm" onClick={(e) => { e.stopPropagation(); onAcknowledge(); }}>
              Acknowledge
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Handoff Detail View
interface HandoffDetailProps {
  handoff: SBARHandoff;
  onClose: () => void;
  onAcknowledge: () => void;
  onComplete: () => void;
  isRecipient: boolean;
}

export function HandoffDetail({ handoff, onClose, onAcknowledge, onComplete, isRecipient }: HandoffDetailProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Shift Handoff</h2>
        <Button variant="ghost" size="icon" onClick={onClose}><X className="h-4 w-4" /></Button>
      </div>

      {/* Header */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Badge variant="outline">{handoff.shiftType.replace("_", " ")}</Badge>
              <HandoffStatusBadge status={handoff.status} />
            </div>
            <span className="text-sm text-muted-foreground">
              {format(new Date(handoff.createdAt), "MMMM d, yyyy - h:mm a")}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Avatar><AvatarFallback>{handoff.fromUserName.split(" ").map((n) => n[0]).join("")}</AvatarFallback></Avatar>
              <div>
                <p className="text-sm font-medium">{handoff.fromUserName}</p>
                <p className="text-xs text-muted-foreground">From</p>
              </div>
            </div>
            <ArrowRight className="h-5 w-5 text-muted-foreground" />
            <div className="flex items-center gap-2">
              <Avatar><AvatarFallback>{handoff.toUserName.split(" ").map((n) => n[0]).join("")}</AvatarFallback></Avatar>
              <div>
                <p className="text-sm font-medium">{handoff.toUserName}</p>
                <p className="text-xs text-muted-foreground">To</p>
              </div>
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-2">Ward: {handoff.ward}</p>
        </CardContent>
      </Card>

      {/* Patients */}
      <div className="space-y-3">
        <h3 className="font-semibold">Patients ({handoff.patients.length})</h3>
        {handoff.patients.map((patient, i) => (
          <SBARPatientView key={patient.id} patient={patient} defaultOpen={i === 0} />
        ))}
      </div>

      {/* Actions */}
      {isRecipient && handoff.status === "pending_acknowledgment" && (
        <div className="flex gap-3">
          <Button onClick={onAcknowledge} className="flex-1">
            <Check className="h-4 w-4 mr-2" />Acknowledge Handoff
          </Button>
        </div>
      )}
      {isRecipient && handoff.status === "acknowledged" && (
        <div className="flex gap-3">
          <Button onClick={onComplete} className="flex-1">
            <CheckCircle2 className="h-4 w-4 mr-2" />Complete Handoff
          </Button>
        </div>
      )}
    </div>
  );
}

// Main Handoff Dashboard
export function HandoffDashboard() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedHandoff, setSelectedHandoff] = useState<SBARHandoff | null>(null);

  const {
    handoffs,
    currentUser,
    isLoadingHandoffs,
    fetchHandoffs,
    createHandoff,
    acknowledgeHandoff,
    completeHandoff,
  } = useCollaborationStore();

  useEffect(() => { fetchHandoffs(); }, [fetchHandoffs]);

  if (showCreateForm) {
    return (
      <div className="max-w-3xl mx-auto">
        <CreateHandoffForm
          onSubmit={async (data) => {
            await createHandoff(data);
            setShowCreateForm(false);
          }}
          onCancel={() => setShowCreateForm(false)}
        />
      </div>
    );
  }

  if (selectedHandoff) {
    const isRecipient = selectedHandoff.toUserId === currentUser?.id;
    return (
      <div className="max-w-3xl mx-auto">
        <HandoffDetail
          handoff={selectedHandoff}
          onClose={() => setSelectedHandoff(null)}
          onAcknowledge={() => acknowledgeHandoff(selectedHandoff.id)}
          onComplete={() => completeHandoff(selectedHandoff.id)}
          isRecipient={isRecipient}
        />
      </div>
    );
  }

  const pendingForMe = handoffs.filter((h) => h.toUserId === currentUser?.id && h.status === "pending_acknowledgment");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <FileText className="h-6 w-6" />Shift Handoffs
        </h1>
        <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="h-4 w-4 mr-2" />New Handoff
        </Button>
      </div>

      {pendingForMe.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-amber-800">
              <AlertTriangle className="h-4 w-4 inline mr-2" />
              {pendingForMe.length} Handoff(s) Pending Your Acknowledgment
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {pendingForMe.map((h) => (
              <HandoffCard
                key={h.id}
                handoff={h}
                onClick={() => setSelectedHandoff(h)}
                onAcknowledge={() => acknowledgeHandoff(h.id)}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {isLoadingHandoffs ? (
        <div className="text-center py-8"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></div>
      ) : handoffs.length === 0 ? (
        <Card><CardContent className="py-8 text-center text-muted-foreground">No handoffs found</CardContent></Card>
      ) : (
        <div className="space-y-3">
          {handoffs.filter((h) => !pendingForMe.includes(h)).map((handoff) => (
            <HandoffCard key={handoff.id} handoff={handoff} onClick={() => setSelectedHandoff(handoff)} />
          ))}
        </div>
      )}
    </div>
  );
}

// Handoffs widget for dashboard
export function HandoffsWidget() {
  const { handoffs, currentUser, fetchHandoffs, acknowledgeHandoff } = useCollaborationStore();

  useEffect(() => { fetchHandoffs(); }, [fetchHandoffs]);

  const pendingCount = handoffs.filter((h) => h.toUserId === currentUser?.id && h.status === "pending_acknowledgment").length;
  const recentHandoffs = handoffs.slice(0, 2);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <FileText className="h-4 w-4" />Handoffs
          </CardTitle>
          {pendingCount > 0 && <Badge variant="destructive">{pendingCount} pending</Badge>}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {recentHandoffs.map((h) => (
          <div key={h.id} className="p-2 rounded-lg hover:bg-muted/50">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{h.ward}</span>
              <HandoffStatusBadge status={h.status} />
            </div>
            <p className="text-xs text-muted-foreground">{h.fromUserName} → {h.toUserName}</p>
          </div>
        ))}
        <Button variant="ghost" className="w-full text-xs">View All Handoffs</Button>
      </CardContent>
    </Card>
  );
}

export default HandoffDashboard;
