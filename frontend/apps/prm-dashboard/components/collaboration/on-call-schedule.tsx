"use client";

// On-Call Schedule Management Components
// EPIC-UX-010: Provider Collaboration Hub - Journey 10.4

import React, { useEffect, useState } from "react";
import { format, addDays, startOfWeek, isSameDay, isToday } from "date-fns";
import {
  Calendar, Phone, Clock, ChevronLeft, ChevronRight, Plus, ArrowLeftRight,
  Download, Bell, User, Check, X, Loader2, Sun, Moon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  useCollaborationStore,
  type OnCallSlot,
  type SwapRequest,
} from "@/lib/store/collaboration-store";

// Current on-call banner
interface CurrentOnCallProps {
  slot: OnCallSlot;
  onContact: () => void;
}

export function CurrentOnCallBanner({ slot, onContact }: CurrentOnCallProps) {
  return (
    <Card className="border-primary bg-primary/5">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Phone className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Currently On-Call: {slot.department}</p>
              <p className="text-lg font-semibold">{slot.userName}</p>
              <p className="text-sm text-muted-foreground">
                Until {slot.endTime} | {slot.phone}
              </p>
            </div>
          </div>
          <Button onClick={onContact}>
            <Phone className="h-4 w-4 mr-2" />Contact
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Calendar day cell
interface DayCellProps {
  date: Date;
  daySlot?: OnCallSlot;
  nightSlot?: OnCallSlot;
  currentUserId: string;
  onSlotClick: (slot: OnCallSlot) => void;
}

function DayCell({ date, daySlot, nightSlot, currentUserId, onSlotClick }: DayCellProps) {
  const isCurrentDay = isToday(date);
  const dayOfWeek = format(date, "EEE");
  const dayNum = format(date, "d");

  return (
    <div className={cn("border-r last:border-r-0 min-h-[120px]", isCurrentDay && "bg-primary/5")}>
      <div className={cn("p-2 text-center border-b", isCurrentDay && "bg-primary text-primary-foreground")}>
        <p className="text-xs">{dayOfWeek}</p>
        <p className="text-lg font-semibold">{dayNum}</p>
      </div>
      <div className="p-1 space-y-1">
        {daySlot && (
          <button
            className={cn(
              "w-full p-2 rounded text-left text-xs hover:bg-muted/50 transition-colors",
              daySlot.userId === currentUserId && "bg-primary/10 border border-primary/30"
            )}
            onClick={() => onSlotClick(daySlot)}
          >
            <div className="flex items-center gap-1 mb-1">
              <Sun className="h-3 w-3 text-amber-500" />
              <span className="font-medium">Day</span>
            </div>
            <p className="truncate">{daySlot.userName.split(" ")[1] || daySlot.userName.split(" ")[0]}</p>
          </button>
        )}
        {nightSlot && (
          <button
            className={cn(
              "w-full p-2 rounded text-left text-xs hover:bg-muted/50 transition-colors",
              nightSlot.userId === currentUserId && "bg-primary/10 border border-primary/30"
            )}
            onClick={() => onSlotClick(nightSlot)}
          >
            <div className="flex items-center gap-1 mb-1">
              <Moon className="h-3 w-3 text-blue-500" />
              <span className="font-medium">Night</span>
            </div>
            <p className="truncate">{nightSlot.userName.split(" ")[1] || nightSlot.userName.split(" ")[0]}</p>
          </button>
        )}
      </div>
    </div>
  );
}

// Swap request dialog
interface SwapRequestDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  slot: OnCallSlot | null;
  onSubmit: (reason: string) => Promise<void>;
}

function SwapRequestDialog({ open, onOpenChange, slot, onSubmit }: SwapRequestDialogProps) {
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    await onSubmit(reason);
    setIsSubmitting(false);
    setReason("");
    onOpenChange(false);
  };

  if (!slot) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Request Shift Swap</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="p-4 bg-muted/50 rounded-lg space-y-2">
            <p className="text-sm font-medium">Shift Details</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><span className="text-muted-foreground">Date:</span> {format(new Date(slot.date), "MMMM d, yyyy")}</div>
              <div><span className="text-muted-foreground">Shift:</span> {slot.shiftType === "day" ? "Day (8AM-8PM)" : "Night (8PM-8AM)"}</div>
              <div><span className="text-muted-foreground">Department:</span> {slot.department}</div>
            </div>
          </div>
          <div className="space-y-2">
            <Label>Reason for Swap Request</Label>
            <Textarea
              placeholder="Please provide a reason for this swap request..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            Your request will be sent to the department coordinator for approval.
            Other providers will be notified and can offer to take this shift.
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={!reason || isSubmitting}>
            {isSubmitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <ArrowLeftRight className="h-4 w-4 mr-2" />}
            Submit Request
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Slot detail dialog
interface SlotDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  slot: OnCallSlot | null;
  isOwnSlot: boolean;
  onRequestSwap: () => void;
  onContact: () => void;
}

function SlotDetailDialog({ open, onOpenChange, slot, isOwnSlot, onRequestSwap, onContact }: SlotDetailDialogProps) {
  if (!slot) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>On-Call Shift Details</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="text-lg">
                {slot.userName.split(" ").map((n) => n[0]).join("")}
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="text-lg font-semibold">{slot.userName}</p>
              <p className="text-sm text-muted-foreground">{slot.department}</p>
              <p className="text-sm text-muted-foreground flex items-center gap-1">
                <Phone className="h-3 w-3" />{slot.phone}
              </p>
            </div>
          </div>
          <Separator />
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Date</p>
              <p className="font-medium">{format(new Date(slot.date), "EEEE, MMMM d, yyyy")}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Shift Type</p>
              <Badge variant="outline" className="mt-1">
                {slot.shiftType === "day" ? <><Sun className="h-3 w-3 mr-1" />Day Shift</> : <><Moon className="h-3 w-3 mr-1" />Night Shift</>}
              </Badge>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Start Time</p>
              <p className="font-medium">{slot.startTime}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">End Time</p>
              <p className="font-medium">{slot.endTime}</p>
            </div>
          </div>
        </div>
        <DialogFooter>
          {isOwnSlot ? (
            <Button variant="outline" onClick={onRequestSwap}>
              <ArrowLeftRight className="h-4 w-4 mr-2" />Request Swap
            </Button>
          ) : (
            <Button onClick={onContact}>
              <Phone className="h-4 w-4 mr-2" />Contact
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Swap requests list
interface SwapRequestsListProps {
  requests: SwapRequest[];
  currentUserId: string;
  onApprove: (id: string) => void;
  onDecline: (id: string) => void;
}

function SwapRequestsList({ requests, currentUserId, onApprove, onDecline }: SwapRequestsListProps) {
  const pendingRequests = requests.filter((r) => r.status === "pending");

  if (pendingRequests.length === 0) {
    return null;
  }

  return (
    <Card className="border-amber-200 bg-amber-50/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-amber-800">Pending Swap Requests</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {pendingRequests.map((request) => (
          <div key={request.id} className="flex items-center justify-between p-3 bg-background rounded-lg">
            <div>
              <p className="text-sm font-medium">{request.requesterName}</p>
              <p className="text-xs text-muted-foreground">{request.reason}</p>
            </div>
            {request.requesterId !== currentUserId && (
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => onDecline(request.id)}>
                  <X className="h-4 w-4" />
                </Button>
                <Button size="sm" onClick={() => onApprove(request.id)}>
                  <Check className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// Main On-Call Schedule Component
export function OnCallSchedule() {
  const [selectedDepartment, setSelectedDepartment] = useState("Cardiology");
  const [weekStart, setWeekStart] = useState(startOfWeek(new Date(), { weekStartsOn: 1 }));
  const [selectedSlot, setSelectedSlot] = useState<OnCallSlot | null>(null);
  const [showSwapRequest, setShowSwapRequest] = useState(false);

  const {
    onCallSchedule,
    currentOnCall,
    swapRequests,
    currentUser,
    isLoadingOnCall,
    fetchOnCallSchedule,
    createSwapRequest,
    approveSwapRequest,
    declineSwapRequest,
  } = useCollaborationStore();

  useEffect(() => {
    const endDate = addDays(weekStart, 6);
    fetchOnCallSchedule(
      selectedDepartment,
      format(weekStart, "yyyy-MM-dd"),
      format(endDate, "yyyy-MM-dd")
    );
  }, [fetchOnCallSchedule, selectedDepartment, weekStart]);

  const currentSlot = currentOnCall[selectedDepartment];
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  const getSlotForDate = (date: Date, shiftType: "day" | "night") => {
    return onCallSchedule.find(
      (s) => s.date === format(date, "yyyy-MM-dd") && s.shiftType === shiftType
    );
  };

  const handleSlotClick = (slot: OnCallSlot) => {
    setSelectedSlot(slot);
  };

  const handleRequestSwap = () => {
    setShowSwapRequest(true);
  };

  const handleSwapSubmit = async (reason: string) => {
    if (selectedSlot) {
      await createSwapRequest({
        originalSlotId: selectedSlot.id,
        reason,
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Calendar className="h-6 w-6" />On-Call Schedule
        </h1>
        <div className="flex gap-2">
          <Select value={selectedDepartment} onValueChange={setSelectedDepartment}>
            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="Cardiology">Cardiology</SelectItem>
              <SelectItem value="Endocrinology">Endocrinology</SelectItem>
              <SelectItem value="Nephrology">Nephrology</SelectItem>
              <SelectItem value="Neurology">Neurology</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
          <Button variant="outline"><Bell className="h-4 w-4 mr-2" />Notify</Button>
        </div>
      </div>

      {/* Current on-call */}
      {currentSlot && (
        <CurrentOnCallBanner
          slot={currentSlot}
          onContact={() => window.open(`tel:${currentSlot.phone}`)}
        />
      )}

      {/* Swap requests */}
      <SwapRequestsList
        requests={swapRequests}
        currentUserId={currentUser?.id || ""}
        onApprove={approveSwapRequest}
        onDecline={declineSwapRequest}
      />

      {/* Calendar */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">
              {format(weekStart, "MMMM yyyy")}
            </CardTitle>
            <div className="flex gap-1">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setWeekStart(addDays(weekStart, -7))}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setWeekStart(startOfWeek(new Date(), { weekStartsOn: 1 }))}
              >
                Today
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setWeekStart(addDays(weekStart, 7))}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoadingOnCall ? (
            <div className="h-[200px] flex items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-7 border-t">
              {weekDays.map((date) => (
                <DayCell
                  key={date.toISOString()}
                  date={date}
                  daySlot={getSlotForDate(date, "day")}
                  nightSlot={getSlotForDate(date, "night")}
                  currentUserId={currentUser?.id || ""}
                  onSlotClick={handleSlotClick}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Legend */}
      <div className="flex items-center gap-6 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Sun className="h-4 w-4 text-amber-500" />
          <span>Day Shift (8AM - 8PM)</span>
        </div>
        <div className="flex items-center gap-2">
          <Moon className="h-4 w-4 text-blue-500" />
          <span>Night Shift (8PM - 8AM)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-4 w-4 bg-primary/10 border border-primary/30 rounded" />
          <span>Your Shifts</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button variant="outline">
          <Plus className="h-4 w-4 mr-2" />Add Coverage
        </Button>
        <Button variant="outline">
          <ArrowLeftRight className="h-4 w-4 mr-2" />Swap Request
        </Button>
      </div>

      {/* Slot detail dialog */}
      <SlotDetailDialog
        open={!!selectedSlot && !showSwapRequest}
        onOpenChange={(open) => !open && setSelectedSlot(null)}
        slot={selectedSlot}
        isOwnSlot={selectedSlot?.userId === currentUser?.id}
        onRequestSwap={handleRequestSwap}
        onContact={() => selectedSlot && window.open(`tel:${selectedSlot.phone}`)}
      />

      {/* Swap request dialog */}
      <SwapRequestDialog
        open={showSwapRequest}
        onOpenChange={setShowSwapRequest}
        slot={selectedSlot}
        onSubmit={handleSwapSubmit}
      />
    </div>
  );
}

// On-Call widget for dashboard
export function OnCallWidget() {
  const { currentOnCall, fetchOnCallSchedule } = useCollaborationStore();

  useEffect(() => {
    const today = new Date();
    fetchOnCallSchedule("Cardiology", format(today, "yyyy-MM-dd"), format(today, "yyyy-MM-dd"));
  }, [fetchOnCallSchedule]);

  const currentSlot = currentOnCall["Cardiology"];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Phone className="h-4 w-4" />On-Call Now
        </CardTitle>
      </CardHeader>
      <CardContent>
        {currentSlot ? (
          <div className="flex items-center gap-3">
            <Avatar>
              <AvatarFallback>{currentSlot.userName.split(" ").map((n) => n[0]).join("")}</AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <p className="text-sm font-medium">{currentSlot.userName}</p>
              <p className="text-xs text-muted-foreground">{currentSlot.department}</p>
            </div>
            <Button size="sm" variant="outline" onClick={() => window.open(`tel:${currentSlot.phone}`)}>
              <Phone className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No on-call information available</p>
        )}
      </CardContent>
    </Card>
  );
}

export default OnCallSchedule;
