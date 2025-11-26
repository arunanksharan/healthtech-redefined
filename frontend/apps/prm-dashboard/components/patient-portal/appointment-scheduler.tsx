"use client";

// Appointment Self-Scheduling
// EPIC-UX-011: Patient Self-Service Portal - Journey 11.2

import React, { useEffect, useState } from "react";
import { format, addDays, startOfWeek, isSameDay, isToday, isPast, isBefore } from "date-fns";
import {
  Calendar, Clock, MapPin, User, ChevronLeft, ChevronRight, Star, Check,
  Video, Building2, Loader2, AlertCircle, X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  usePatientPortalStore,
  type Appointment,
  type AvailableSlot,
} from "@/lib/store/patient-portal-store";

// Visit types
const VISIT_TYPES = [
  { id: "followup", label: "Follow-up visit", description: "Existing condition" },
  { id: "new", label: "New concern or symptom", description: "Something new to discuss" },
  { id: "physical", label: "Annual physical / Wellness check", description: "Routine checkup" },
  { id: "telehealth", label: "Telehealth visit", description: "Video call with provider" },
];

// Mock providers
const PROVIDERS = [
  { id: "doc1", name: "Dr. Rohit Sharma", specialty: "Cardiology", rating: 4.8, nextAvailable: "Dec 23, 2024", isPrimary: true },
  { id: "doc2", name: "Dr. Priya Mehta", specialty: "Endocrinology", rating: 4.9, nextAvailable: "Dec 20, 2024" },
  { id: "doc3", name: "Dr. Arun Gupta", specialty: "Nephrology", rating: 4.7, nextAvailable: "Dec 22, 2024" },
];

// Step indicator
function StepIndicator({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>Step {currentStep} of {totalSteps}</span>
      </div>
      <Progress value={(currentStep / totalSteps) * 100} className="h-2" />
    </div>
  );
}

// Provider selection card
interface ProviderCardProps {
  provider: typeof PROVIDERS[0];
  isSelected: boolean;
  onSelect: () => void;
}

function ProviderCard({ provider, isSelected, onSelect }: ProviderCardProps) {
  return (
    <Card
      className={cn(
        "cursor-pointer transition-all hover:shadow-md",
        isSelected && "border-primary ring-1 ring-primary"
      )}
      onClick={onSelect}
    >
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Avatar className="h-12 w-12">
              <AvatarFallback>{provider.name.split(" ").map((n) => n[0]).join("")}</AvatarFallback>
            </Avatar>
            {isSelected && (
              <div className="absolute -top-1 -right-1 h-5 w-5 bg-primary rounded-full flex items-center justify-center">
                <Check className="h-3 w-3 text-primary-foreground" />
              </div>
            )}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <p className="font-semibold">{provider.name}</p>
              {provider.rating && (
                <span className="flex items-center gap-1 text-sm text-amber-600">
                  <Star className="h-3 w-3 fill-current" />{provider.rating}
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{provider.specialty}</p>
            {provider.isPrimary && (
              <Badge variant="secondary" className="mt-1 text-xs">Your primary provider</Badge>
            )}
          </div>
          <div className="text-right text-sm text-muted-foreground">
            <p>Next available:</p>
            <p className="font-medium text-foreground">{provider.nextAvailable}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Calendar for date selection
interface DateCalendarProps {
  selectedDate: Date | null;
  onSelectDate: (date: Date) => void;
  availableDates: string[];
}

function DateCalendar({ selectedDate, onSelectDate, availableDates }: DateCalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const weekStart = startOfWeek(currentMonth, { weekStartsOn: 0 });

  const days = Array.from({ length: 35 }, (_, i) => addDays(weekStart, i));
  const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  const isAvailable = (date: Date) => {
    return availableDates.includes(format(date, "yyyy-MM-dd")) && !isPast(date);
  };

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <Button variant="ghost" size="icon" onClick={() => setCurrentMonth(addDays(currentMonth, -30))}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="font-medium">{format(currentMonth, "MMMM yyyy")}</span>
        <Button variant="ghost" size="icon" onClick={() => setCurrentMonth(addDays(currentMonth, 30))}>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
      <div className="grid grid-cols-7 gap-1">
        {weekDays.map((day) => (
          <div key={day} className="text-center text-xs text-muted-foreground py-2">{day}</div>
        ))}
        {days.map((date, i) => {
          const available = isAvailable(date);
          const selected = selectedDate && isSameDay(date, selectedDate);
          const today = isToday(date);

          return (
            <button
              key={i}
              className={cn(
                "p-2 text-sm rounded-lg transition-colors",
                available ? "hover:bg-primary/10 cursor-pointer" : "text-muted-foreground/50 cursor-not-allowed",
                selected && "bg-primary text-primary-foreground hover:bg-primary",
                today && !selected && "border border-primary"
              )}
              onClick={() => available && onSelectDate(date)}
              disabled={!available}
            >
              {format(date, "d")}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// Time slot selection
interface TimeSlotsProps {
  slots: AvailableSlot[];
  selectedSlot: AvailableSlot | null;
  onSelectSlot: (slot: AvailableSlot) => void;
}

function TimeSlots({ slots, selectedSlot, onSelectSlot }: TimeSlotsProps) {
  const morningSlots = slots.filter((s) => parseInt(s.time.split(":")[0]) < 12);
  const afternoonSlots = slots.filter((s) => parseInt(s.time.split(":")[0]) >= 12);

  const TimeButton = ({ slot }: { slot: AvailableSlot }) => {
    const isSelected = selectedSlot?.time === slot.time && selectedSlot?.date === slot.date;
    return (
      <button
        className={cn(
          "px-4 py-2 rounded-lg border text-sm transition-colors",
          isSelected
            ? "bg-primary text-primary-foreground border-primary"
            : "hover:bg-muted hover:border-primary/50"
        )}
        onClick={() => onSelectSlot(slot)}
      >
        {format(new Date(`2024-01-01T${slot.time}`), "h:mm a")}
      </button>
    );
  };

  return (
    <div className="space-y-4">
      {morningSlots.length > 0 && (
        <div>
          <p className="text-sm font-medium mb-2">Morning</p>
          <div className="flex flex-wrap gap-2">
            {morningSlots.map((slot) => (
              <TimeButton key={`${slot.date}-${slot.time}`} slot={slot} />
            ))}
          </div>
        </div>
      )}
      {afternoonSlots.length > 0 && (
        <div>
          <p className="text-sm font-medium mb-2">Afternoon</p>
          <div className="flex flex-wrap gap-2">
            {afternoonSlots.map((slot) => (
              <TimeButton key={`${slot.date}-${slot.time}`} slot={slot} />
            ))}
          </div>
        </div>
      )}
      {slots.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-4">
          No available times for this date
        </p>
      )}
    </div>
  );
}

// Booking confirmation
interface BookingConfirmationProps {
  slot: AvailableSlot;
  visitType: string;
  provider: typeof PROVIDERS[0];
  notes: string;
  onConfirm: () => void;
  onBack: () => void;
  isBooking: boolean;
}

function BookingConfirmation({ slot, visitType, provider, notes, onConfirm, onBack, isBooking }: BookingConfirmationProps) {
  const visitTypeLabel = VISIT_TYPES.find((v) => v.id === visitType)?.label || visitType;

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Confirm Your Appointment</h2>

      <Card>
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
              <Calendar className="h-8 w-8 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {format(new Date(slot.date), "EEEE, MMMM d")}
              </p>
              <p className="text-lg text-muted-foreground">
                {format(new Date(`2024-01-01T${slot.time}`), "h:mm a")}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div className="flex items-center gap-3">
              <User className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Provider</p>
                <p className="font-medium">{provider.name}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Building2 className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Location</p>
                <p className="font-medium">{slot.locationName}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Visit Type</p>
                <p className="font-medium">{visitTypeLabel}</p>
              </div>
            </div>
          </div>

          {notes && (
            <div className="pt-4 border-t">
              <p className="text-sm text-muted-foreground">Notes for provider:</p>
              <p className="text-sm mt-1">{notes}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="flex-1">Back</Button>
        <Button onClick={onConfirm} disabled={isBooking} className="flex-1">
          {isBooking ? (
            <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Booking...</>
          ) : (
            "Confirm Appointment"
          )}
        </Button>
      </div>
    </div>
  );
}

// Main Appointment Scheduler Component
export function AppointmentScheduler() {
  const [step, setStep] = useState(1);
  const [visitType, setVisitType] = useState("");
  const [selectedProvider, setSelectedProvider] = useState<typeof PROVIDERS[0] | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<AvailableSlot | null>(null);
  const [notes, setNotes] = useState("");
  const [showSuccess, setShowSuccess] = useState(false);

  const {
    availableSlots,
    isBookingAppointment,
    searchAvailableSlots,
    bookAppointment,
  } = usePatientPortalStore();

  useEffect(() => {
    if (selectedProvider && selectedDate) {
      const startDate = format(selectedDate, "yyyy-MM-dd");
      const endDate = format(addDays(selectedDate, 7), "yyyy-MM-dd");
      searchAvailableSlots(selectedProvider.id, startDate, endDate);
    }
  }, [selectedProvider, selectedDate, searchAvailableSlots]);

  const handleBook = async () => {
    if (selectedSlot && visitType) {
      await bookAppointment(selectedSlot, visitType, notes);
      setShowSuccess(true);
    }
  };

  const availableDates = [...new Set(availableSlots.map((s) => s.date))];
  const slotsForSelectedDate = selectedDate
    ? availableSlots.filter((s) => s.date === format(selectedDate, "yyyy-MM-dd"))
    : [];

  // Success dialog
  if (showSuccess) {
    return (
      <div className="max-w-xl mx-auto text-center py-12">
        <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
          <Check className="h-8 w-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-semibold mb-2">Appointment Booked!</h2>
        <p className="text-muted-foreground mb-6">
          Your appointment has been scheduled. You'll receive a confirmation email shortly.
        </p>
        <Button onClick={() => window.location.reload()}>
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Calendar className="h-6 w-6" />Book an Appointment
        </h1>
      </div>

      <StepIndicator currentStep={step} totalSteps={3} />

      {/* Step 1: Visit Type & Provider */}
      {step === 1 && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">What type of appointment do you need?</CardTitle>
            </CardHeader>
            <CardContent>
              <RadioGroup value={visitType} onValueChange={setVisitType} className="space-y-2">
                {VISIT_TYPES.map((type) => (
                  <div
                    key={type.id}
                    className={cn(
                      "flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors",
                      visitType === type.id && "border-primary bg-primary/5"
                    )}
                    onClick={() => setVisitType(type.id)}
                  >
                    <RadioGroupItem value={type.id} id={type.id} />
                    <Label htmlFor={type.id} className="flex-1 cursor-pointer">
                      <p className="font-medium">{type.label}</p>
                      <p className="text-sm text-muted-foreground">{type.description}</p>
                    </Label>
                    {type.id === "telehealth" && <Video className="h-5 w-5 text-blue-500" />}
                  </div>
                ))}
              </RadioGroup>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Select Provider</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground mb-3">Your care team:</p>
              {PROVIDERS.map((provider) => (
                <ProviderCard
                  key={provider.id}
                  provider={provider}
                  isSelected={selectedProvider?.id === provider.id}
                  onSelect={() => setSelectedProvider(provider)}
                />
              ))}
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button
              onClick={() => setStep(2)}
              disabled={!visitType || !selectedProvider}
            >
              Continue <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 2: Date & Time */}
      {step === 2 && selectedProvider && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center justify-between">
                <span>{selectedProvider.name} - {VISIT_TYPES.find((v) => v.id === visitType)?.label}</span>
                <Badge variant="outline"><MapPin className="h-3 w-3 mr-1" />Surya Whitefield</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <DateCalendar
                selectedDate={selectedDate}
                onSelectDate={setSelectedDate}
                availableDates={availableDates}
              />

              {selectedDate && (
                <>
                  <div>
                    <p className="text-sm font-medium mb-3">
                      Available times for {format(selectedDate, "MMMM d")}:
                    </p>
                    <TimeSlots
                      slots={slotsForSelectedDate}
                      selectedSlot={selectedSlot}
                      onSelectSlot={setSelectedSlot}
                    />
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <div className="space-y-2">
            <Label>Notes for provider (optional)</Label>
            <Textarea
              placeholder="Any additional information for your visit..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
          </div>

          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setStep(1)}>
              <ChevronLeft className="h-4 w-4 mr-1" />Back
            </Button>
            <Button onClick={() => setStep(3)} disabled={!selectedSlot}>
              Continue <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Confirmation */}
      {step === 3 && selectedSlot && selectedProvider && (
        <BookingConfirmation
          slot={selectedSlot}
          visitType={visitType}
          provider={selectedProvider}
          notes={notes}
          onConfirm={handleBook}
          onBack={() => setStep(2)}
          isBooking={isBookingAppointment}
        />
      )}
    </div>
  );
}

export default AppointmentScheduler;
