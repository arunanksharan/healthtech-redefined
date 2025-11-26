"use client";

import * as React from "react";
import {
  User,
  Phone,
  Mail,
  MapPin,
  Calendar,
  Star,
  MoreHorizontal,
  Clock,
  Activity,
  Stethoscope,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { StatusBadge } from "./entity-list";
import type { Practitioner, Department, Location } from "@/lib/store/organization-store";
import { format } from "date-fns";

// ============================================================================
// Practitioner Card Component
// ============================================================================

interface PractitionerCardProps {
  practitioner: Practitioner;
  department?: Department;
  location?: Location;
  compact?: boolean;
  onClick?: () => void;
  onSchedule?: () => void;
  onEdit?: () => void;
  className?: string;
}

export function PractitionerCard({
  practitioner,
  department,
  location,
  compact = false,
  onClick,
  onSchedule,
  onEdit,
  className,
}: PractitionerCardProps) {
  if (compact) {
    return (
      <div
        className={cn(
          "flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors cursor-pointer",
          className
        )}
        onClick={onClick}
      >
        <Avatar className="h-10 w-10">
          <AvatarImage src={practitioner.photo} />
          <AvatarFallback className="bg-primary/10 text-primary text-sm">
            {practitioner.firstName[0]}
            {practitioner.lastName[0]}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">{practitioner.name}</p>
          <p className="text-xs text-muted-foreground truncate">
            {practitioner.specialties[0]}
          </p>
        </div>
        <StatusBadge status={practitioner.status} />
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </div>
    );
  }

  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          {/* Avatar and Basic Info */}
          <div className="flex items-start gap-4">
            <Avatar className="h-16 w-16">
              <AvatarImage src={practitioner.photo} />
              <AvatarFallback className="bg-primary/10 text-primary text-lg">
                {practitioner.firstName[0]}
                {practitioner.lastName[0]}
              </AvatarFallback>
            </Avatar>
            <div>
              <h3
                className="font-semibold text-lg hover:text-primary cursor-pointer"
                onClick={onClick}
              >
                {practitioner.name}
              </h3>
              <p className="text-sm text-muted-foreground">
                {practitioner.qualifications.join(", ")}
              </p>
              <div className="flex items-center gap-2 mt-2">
                <StatusBadge status={practitioner.status} />
                {practitioner.rating && (
                  <span className="text-sm flex items-center gap-1">
                    <Star className="h-3 w-3 fill-warning text-warning" />
                    {practitioner.rating}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Actions Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onClick}>View Profile</DropdownMenuItem>
              <DropdownMenuItem onClick={onSchedule}>View Schedule</DropdownMenuItem>
              <DropdownMenuItem onClick={onEdit}>Edit</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Set Leave</DropdownMenuItem>
              <DropdownMenuItem className="text-destructive">Deactivate</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Details */}
        <div className="mt-4 grid grid-cols-3 gap-4">
          {/* Location & Department */}
          <div className="space-y-1">
            {location && (
              <div className="flex items-center gap-1.5 text-sm">
                <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="truncate">{location.name}</span>
              </div>
            )}
            {department && (
              <div className="flex items-center gap-1.5 text-sm">
                <Stethoscope className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="truncate">{department.name}</span>
              </div>
            )}
          </div>

          {/* Specialties */}
          <div className="flex flex-wrap gap-1">
            {practitioner.specialties.slice(0, 2).map((specialty) => (
              <Badge key={specialty} variant="secondary" className="text-xs">
                {specialty}
              </Badge>
            ))}
          </div>

          {/* Stats */}
          <div className="text-right">
            {practitioner.totalAppointments !== undefined && (
              <p className="text-sm">
                <span className="font-medium">{practitioner.totalAppointments}</span>
                <span className="text-muted-foreground ml-1">appts</span>
              </p>
            )}
            {practitioner.noShowRate !== undefined && (
              <p className="text-xs text-muted-foreground">
                {practitioner.noShowRate}% no-show
              </p>
            )}
          </div>
        </div>

        {/* Leave Status */}
        {practitioner.status === "on_leave" && practitioner.leaveStart && practitioner.leaveEnd && (
          <div className="mt-4 p-2 bg-warning/10 rounded-lg border border-warning/20">
            <p className="text-sm text-warning">
              On leave: {format(new Date(practitioner.leaveStart), "MMM d")} -{" "}
              {format(new Date(practitioner.leaveEnd), "MMM d, yyyy")}
            </p>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-4 flex items-center gap-2">
          <Button variant="outline" size="sm" className="flex-1" onClick={onSchedule}>
            <Calendar className="h-4 w-4 mr-2" />
            View Schedule
          </Button>
          <Button variant="outline" size="sm" onClick={onClick}>
            <Activity className="h-4 w-4 mr-2" />
            Analytics
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Practitioner List Component
// ============================================================================

interface PractitionerListProps {
  practitioners: Practitioner[];
  departments: Department[];
  locations: Location[];
  selectedDepartment?: string;
  selectedLocation?: string;
  searchQuery?: string;
  view?: "grid" | "list";
  isLoading?: boolean;
  onPractitionerClick?: (practitioner: Practitioner) => void;
  onScheduleClick?: (practitioner: Practitioner) => void;
  onEditClick?: (practitioner: Practitioner) => void;
  onAddClick?: () => void;
  className?: string;
}

export function PractitionerList({
  practitioners,
  departments,
  locations,
  selectedDepartment,
  selectedLocation,
  searchQuery,
  view = "grid",
  isLoading = false,
  onPractitionerClick,
  onScheduleClick,
  onEditClick,
  onAddClick,
  className,
}: PractitionerListProps) {
  // Filter practitioners
  let filteredPractitioners = practitioners;

  if (selectedDepartment && selectedDepartment !== "all") {
    filteredPractitioners = filteredPractitioners.filter((p) =>
      p.departmentIds.includes(selectedDepartment)
    );
  }

  if (selectedLocation && selectedLocation !== "all") {
    filteredPractitioners = filteredPractitioners.filter((p) =>
      p.locationIds.includes(selectedLocation)
    );
  }

  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    filteredPractitioners = filteredPractitioners.filter(
      (p) =>
        p.name.toLowerCase().includes(query) ||
        p.specialties.some((s) => s.toLowerCase().includes(query))
    );
  }

  const getDepartment = (practitioner: Practitioner) =>
    departments.find((d) => practitioner.departmentIds.includes(d.id));

  const getLocation = (practitioner: Practitioner) =>
    locations.find((l) => practitioner.locationIds.includes(l.id));

  if (isLoading) {
    return (
      <div className={cn("grid gap-4", view === "grid" ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" : "", className)}>
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="h-16 w-16 rounded-full bg-muted" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 bg-muted rounded w-2/3" />
                  <div className="h-4 bg-muted rounded w-1/2" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (filteredPractitioners.length === 0) {
    return (
      <div className="text-center py-12">
        <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-medium mb-2">No practitioners found</h3>
        <p className="text-sm text-muted-foreground mb-4">
          {searchQuery ? "Try adjusting your search query" : "Add practitioners to get started"}
        </p>
        {onAddClick && (
          <Button onClick={onAddClick}>Add Practitioner</Button>
        )}
      </div>
    );
  }

  if (view === "list") {
    return (
      <div className={cn("space-y-2", className)}>
        {filteredPractitioners.map((practitioner) => (
          <PractitionerCard
            key={practitioner.id}
            practitioner={practitioner}
            department={getDepartment(practitioner)}
            location={getLocation(practitioner)}
            compact
            onClick={() => onPractitionerClick?.(practitioner)}
          />
        ))}
      </div>
    );
  }

  return (
    <div className={cn("grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3", className)}>
      {filteredPractitioners.map((practitioner) => (
        <PractitionerCard
          key={practitioner.id}
          practitioner={practitioner}
          department={getDepartment(practitioner)}
          location={getLocation(practitioner)}
          onClick={() => onPractitionerClick?.(practitioner)}
          onSchedule={() => onScheduleClick?.(practitioner)}
          onEdit={() => onEditClick?.(practitioner)}
        />
      ))}
    </div>
  );
}

// ============================================================================
// Practitioner Detail Header
// ============================================================================

interface PractitionerDetailHeaderProps {
  practitioner: Practitioner;
  department?: Department;
  location?: Location;
  onEdit?: () => void;
  onBack?: () => void;
  className?: string;
}

export function PractitionerDetailHeader({
  practitioner,
  department,
  location,
  onEdit,
  onBack,
  className,
}: PractitionerDetailHeaderProps) {
  return (
    <Card className={className}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-6">
            <Avatar className="h-24 w-24">
              <AvatarImage src={practitioner.photo} />
              <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                {practitioner.firstName[0]}
                {practitioner.lastName[0]}
              </AvatarFallback>
            </Avatar>

            <div className="space-y-3">
              <div>
                <h1 className="text-2xl font-bold">{practitioner.name}</h1>
                <p className="text-muted-foreground">
                  {practitioner.qualifications.join(", ")}
                </p>
              </div>

              <div className="flex items-center gap-4 text-sm">
                {practitioner.contact?.phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    {practitioner.contact.phone}
                  </div>
                )}
                {practitioner.contact?.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    {practitioner.contact.email}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                {location && (
                  <Badge variant="outline">
                    <MapPin className="h-3 w-3 mr-1" />
                    {location.name}
                  </Badge>
                )}
                {department && (
                  <Badge variant="outline">
                    <Stethoscope className="h-3 w-3 mr-1" />
                    {department.name}
                  </Badge>
                )}
                <StatusBadge status={practitioner.status} />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={onEdit}>
              Edit Profile
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>Set Leave</DropdownMenuItem>
                <DropdownMenuItem>Block Time</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive">Deactivate</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Practitioner Stats Card
// ============================================================================

interface PractitionerStatsProps {
  practitioner: Practitioner;
  className?: string;
}

export function PractitionerStats({ practitioner, className }: PractitionerStatsProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-sm">Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <p className="text-2xl font-bold">{practitioner.totalAppointments || 0}</p>
            <p className="text-xs text-muted-foreground">This Month</p>
          </div>
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <p className="text-2xl font-bold">{practitioner.noShowRate || 0}%</p>
            <p className="text-xs text-muted-foreground">No-Show Rate</p>
          </div>
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <p className="text-2xl font-bold flex items-center justify-center gap-1">
              {practitioner.rating || "-"}
              {practitioner.rating && <Star className="h-4 w-4 fill-warning text-warning" />}
            </p>
            <p className="text-xs text-muted-foreground">Avg Rating</p>
          </div>
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <p className="text-2xl font-bold">
              {practitioner.status === "active" ? "Yes" : "No"}
            </p>
            <p className="text-xs text-muted-foreground">Available</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default PractitionerCard;
