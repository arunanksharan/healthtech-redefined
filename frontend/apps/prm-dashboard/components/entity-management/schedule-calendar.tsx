"use client";

import * as React from "react";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Calendar as CalendarIcon,
  Clock,
  User,
  MoreHorizontal,
  Mic,
  X,
  Ban,
  Download,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Slot, Appointment, Practitioner, Department } from "@/lib/store/organization-store";
import {
  format,
  startOfWeek,
  addDays,
  addWeeks,
  subWeeks,
  isSameDay,
  isToday,
  eachDayOfInterval,
  startOfMonth,
  endOfMonth,
  getDay,
} from "date-fns";

// ============================================================================
// Types
// ============================================================================

interface ScheduleCalendarProps {
  view: "day" | "week" | "month";
  currentDate: Date;
  practitioners: Practitioner[];
  slots: Slot[];
  appointments: Appointment[];
  departments: Department[];
  selectedDepartment?: string;
  selectedPractitioner?: string;
  onViewChange: (view: "day" | "week" | "month") => void;
  onDateChange: (date: Date) => void;
  onDepartmentChange: (departmentId: string) => void;
  onPractitionerChange: (practitionerId: string) => void;
  onSlotCreate: (slot: Partial<Slot>) => void;
  onSlotUpdate: (slotId: string, updates: Partial<Slot>) => void;
  onSlotDelete: (slotId: string) => void;
  onAppointmentClick: (appointment: Appointment) => void;
  onVoiceCommand?: () => void;
  className?: string;
}

// ============================================================================
// Slot Card Component
// ============================================================================

interface SlotCardProps {
  slot: Slot;
  appointments: Appointment[];
  practitioner?: Practitioner;
  onEdit?: () => void;
  onDelete?: () => void;
  onAppointmentClick?: (appointment: Appointment) => void;
}

export function SlotCard({
  slot,
  appointments,
  practitioner,
  onEdit,
  onDelete,
  onAppointmentClick,
}: SlotCardProps) {
  const slotAppointments = appointments.filter(
    (apt) =>
      apt.practitionerId === slot.practitionerId &&
      new Date(apt.start) >= new Date(slot.start) &&
      new Date(apt.end) <= new Date(slot.end)
  );

  const getStatusColor = () => {
    switch (slot.status) {
      case "free":
        return "bg-success/20 border-success/30 hover:bg-success/30";
      case "busy":
        return "bg-warning/20 border-warning/30";
      case "busy-unavailable":
        return "bg-muted border-muted-foreground/30";
      case "busy-tentative":
        return "bg-blue-500/20 border-blue-500/30";
      default:
        return "bg-muted";
    }
  };

  const duration = Math.round(
    (new Date(slot.end).getTime() - new Date(slot.start).getTime()) / (1000 * 60)
  );
  const height = Math.max(40, (duration / 60) * 60); // 60px per hour minimum

  return (
    <div
      className={cn(
        "rounded-lg border p-2 transition-colors cursor-pointer group relative",
        getStatusColor()
      )}
      style={{ minHeight: `${height}px` }}
      onClick={onEdit}
    >
      {/* Time */}
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="font-medium">
          {format(new Date(slot.start), "h:mm a")} - {format(new Date(slot.end), "h:mm a")}
        </span>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 opacity-0 group-hover:opacity-100"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={onEdit}>Edit Slot</DropdownMenuItem>
            <DropdownMenuItem>Copy Slot</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive" onClick={onDelete}>
              Delete Slot
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Practitioner */}
      {practitioner && (
        <p className="text-xs text-muted-foreground truncate">
          {practitioner.name}
        </p>
      )}

      {/* Appointment count */}
      {slotAppointments.length > 0 && (
        <div className="mt-2 space-y-1">
          {slotAppointments.slice(0, 3).map((apt) => (
            <div
              key={apt.id}
              className="text-xs p-1 bg-background/80 rounded cursor-pointer hover:bg-background"
              onClick={(e) => {
                e.stopPropagation();
                onAppointmentClick?.(apt);
              }}
            >
              <span className="font-medium">{apt.patientName}</span>
              <span className="text-muted-foreground ml-1">
                {format(new Date(apt.start), "h:mm a")}
              </span>
            </div>
          ))}
          {slotAppointments.length > 3 && (
            <p className="text-xs text-muted-foreground">
              +{slotAppointments.length - 3} more
            </p>
          )}
        </div>
      )}

      {/* Empty slot indicator */}
      {slot.status === "free" && slotAppointments.length === 0 && (
        <div className="flex items-center gap-1 text-xs text-success mt-1">
          <span>Available</span>
        </div>
      )}

      {/* Blocked indicator */}
      {slot.status === "busy-unavailable" && (
        <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
          <Ban className="h-3 w-3" />
          <span>{slot.comment || "Blocked"}</span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Week View
// ============================================================================

interface WeekViewProps {
  startDate: Date;
  practitioners: Practitioner[];
  slots: Slot[];
  appointments: Appointment[];
  selectedPractitioner?: string;
  onSlotClick: (slot: Slot) => void;
  onSlotCreate: (date: Date, practitionerId: string) => void;
  onAppointmentClick: (appointment: Appointment) => void;
}

function WeekView({
  startDate,
  practitioners,
  slots,
  appointments,
  selectedPractitioner,
  onSlotClick,
  onSlotCreate,
  onAppointmentClick,
}: WeekViewProps) {
  const weekStart = startOfWeek(startDate, { weekStartsOn: 1 });
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  // Filter practitioners if one is selected
  const displayPractitioners = selectedPractitioner && selectedPractitioner !== "all"
    ? practitioners.filter((p) => p.id === selectedPractitioner)
    : practitioners.slice(0, 4); // Show max 4 practitioners in week view

  const getSlotsForDay = (date: Date, practitionerId: string) => {
    return slots.filter(
      (slot) =>
        slot.practitionerId === practitionerId &&
        isSameDay(new Date(slot.start), date)
    );
  };

  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-muted/50">
            <th className="p-2 text-left text-xs font-medium text-muted-foreground w-32 border-r">
              Practitioner
            </th>
            {weekDays.map((day) => (
              <th
                key={day.toISOString()}
                className={cn(
                  "p-2 text-center text-xs font-medium border-r last:border-r-0",
                  isToday(day) ? "bg-primary/10 text-primary" : "text-muted-foreground"
                )}
              >
                <div>{format(day, "EEE")}</div>
                <div className={cn("text-lg font-semibold", isToday(day) && "text-primary")}>
                  {format(day, "d")}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayPractitioners.map((practitioner) => (
            <tr key={practitioner.id} className="border-t">
              <td className="p-2 border-r align-top">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium text-primary">
                    {practitioner.firstName[0]}
                    {practitioner.lastName[0]}
                  </div>
                  <div>
                    <p className="text-sm font-medium truncate max-w-24">{practitioner.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {practitioner.specialties[0]}
                    </p>
                  </div>
                </div>
              </td>
              {weekDays.map((day) => {
                const daySlots = getSlotsForDay(day, practitioner.id);
                const isWeekend = getDay(day) === 0 || getDay(day) === 6;

                return (
                  <td
                    key={day.toISOString()}
                    className={cn(
                      "p-1 border-r last:border-r-0 align-top min-h-[100px]",
                      isWeekend && "bg-muted/30"
                    )}
                  >
                    <div className="space-y-1 min-h-[80px]">
                      {daySlots.map((slot) => (
                        <SlotCard
                          key={slot.id}
                          slot={slot}
                          appointments={appointments}
                          onEdit={() => onSlotClick(slot)}
                          onAppointmentClick={onAppointmentClick}
                        />
                      ))}
                      {daySlots.length === 0 && !isWeekend && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="w-full h-16 border-2 border-dashed text-muted-foreground hover:text-foreground"
                          onClick={() => onSlotCreate(day, practitioner.id)}
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ============================================================================
// Schedule Calendar Component
// ============================================================================

export function ScheduleCalendar({
  view,
  currentDate,
  practitioners,
  slots,
  appointments,
  departments,
  selectedDepartment,
  selectedPractitioner,
  onViewChange,
  onDateChange,
  onDepartmentChange,
  onPractitionerChange,
  onSlotCreate,
  onSlotUpdate,
  onSlotDelete,
  onAppointmentClick,
  onVoiceCommand,
  className,
}: ScheduleCalendarProps) {
  const navigatePrev = () => {
    if (view === "week") {
      onDateChange(subWeeks(currentDate, 1));
    } else if (view === "day") {
      onDateChange(addDays(currentDate, -1));
    } else {
      onDateChange(addDays(startOfMonth(currentDate), -1));
    }
  };

  const navigateNext = () => {
    if (view === "week") {
      onDateChange(addWeeks(currentDate, 1));
    } else if (view === "day") {
      onDateChange(addDays(currentDate, 1));
    } else {
      onDateChange(addDays(endOfMonth(currentDate), 1));
    }
  };

  const navigateToday = () => {
    onDateChange(new Date());
  };

  const getDateRangeLabel = () => {
    if (view === "day") {
      return format(currentDate, "EEEE, MMMM d, yyyy");
    } else if (view === "week") {
      const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });
      const weekEnd = addDays(weekStart, 6);
      return `${format(weekStart, "MMM d")} - ${format(weekEnd, "MMM d, yyyy")}`;
    } else {
      return format(currentDate, "MMMM yyyy");
    }
  };

  // Filter practitioners by department
  const filteredPractitioners = selectedDepartment && selectedDepartment !== "all"
    ? practitioners.filter((p) => p.departmentIds.includes(selectedDepartment))
    : practitioners;

  return (
    <Card className={className}>
      <CardHeader className="pb-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Title and Voice Command */}
          <div className="flex items-center gap-3">
            <CardTitle>Schedule Management</CardTitle>
            {onVoiceCommand && (
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={onVoiceCommand}
              >
                <Mic className="h-4 w-4" />
                Voice Command
              </Button>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Slot
            </Button>
            <Button variant="outline" size="sm">
              <CalendarIcon className="h-4 w-4 mr-2" />
              Set Recurring
            </Button>
            <Button variant="outline" size="sm">
              <Ban className="h-4 w-4 mr-2" />
              Block Time
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Filters and Navigation */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Department and Practitioner Filters */}
          <div className="flex items-center gap-2">
            <Select
              value={selectedDepartment || "all"}
              onValueChange={onDepartmentChange}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All Departments" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Departments</SelectItem>
                {departments.map((dept) => (
                  <SelectItem key={dept.id} value={dept.id}>
                    {dept.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={selectedPractitioner || "all"}
              onValueChange={onPractitionerChange}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="All Practitioners" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Practitioners</SelectItem>
                {filteredPractitioners.map((prac) => (
                  <SelectItem key={prac.id} value={prac.id}>
                    {prac.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Date Navigation */}
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={navigateToday}>
              Today
            </Button>
            <Button variant="outline" size="icon" onClick={navigatePrev}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm font-medium min-w-[200px] text-center">
              {getDateRangeLabel()}
            </span>
            <Button variant="outline" size="icon" onClick={navigateNext}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          {/* View Toggle */}
          <div className="flex items-center gap-1 p-1 bg-muted rounded-lg">
            {(["day", "week", "month"] as const).map((v) => (
              <Button
                key={v}
                variant={view === v ? "secondary" : "ghost"}
                size="sm"
                className="capitalize"
                onClick={() => onViewChange(v)}
              >
                {v}
              </Button>
            ))}
          </div>
        </div>

        {/* Calendar View */}
        {view === "week" && (
          <WeekView
            startDate={currentDate}
            practitioners={filteredPractitioners}
            slots={slots}
            appointments={appointments}
            selectedPractitioner={selectedPractitioner}
            onSlotClick={(slot) => console.log("Slot clicked:", slot)}
            onSlotCreate={(date, practitionerId) =>
              onSlotCreate({ start: date, practitionerId })
            }
            onAppointmentClick={onAppointmentClick}
          />
        )}

        {view === "day" && (
          <div className="text-center py-12 text-muted-foreground">
            Day view coming soon...
          </div>
        )}

        {view === "month" && (
          <div className="text-center py-12 text-muted-foreground">
            Month view coming soon...
          </div>
        )}

        {/* Legend */}
        <div className="flex items-center gap-4 pt-4 border-t text-xs text-muted-foreground">
          <span className="font-medium">Legend:</span>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-success/40" />
            <span>Available</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-warning/40" />
            <span>Busy</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-muted" />
            <span>Blocked</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-destructive/40" />
            <span>Overbooked</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default ScheduleCalendar;
