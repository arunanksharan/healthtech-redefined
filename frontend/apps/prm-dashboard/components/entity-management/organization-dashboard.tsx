"use client";

import * as React from "react";
import {
  Building,
  MapPin,
  Phone,
  Mail,
  Users,
  Stethoscope,
  Calendar,
  BarChart3,
  Plus,
  ChevronRight,
  Settings,
  MoreHorizontal,
  Clock,
  Globe,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { StatusBadge } from "./entity-list";
import type { Organization, Location, Department, Practitioner } from "@/lib/store/organization-store";

// ============================================================================
// Location Card Component
// ============================================================================

interface LocationCardProps {
  location: Location;
  departments: Department[];
  practitionerCount: number;
  onClick?: () => void;
  onSchedule?: () => void;
  onManageStaff?: () => void;
  onAnalytics?: () => void;
  onEdit?: () => void;
  className?: string;
}

export function LocationCard({
  location,
  departments,
  practitionerCount,
  onClick,
  onSchedule,
  onManageStaff,
  onAnalytics,
  onEdit,
  className,
}: LocationCardProps) {
  const locationDepartments = departments.filter((d) => d.locationId === location.id);

  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            {/* Icon */}
            <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
              <Building className="h-6 w-6 text-primary" />
            </div>

            {/* Info */}
            <div>
              <div className="flex items-center gap-2">
                <h3
                  className="font-semibold text-lg hover:text-primary cursor-pointer"
                  onClick={onClick}
                >
                  {location.name}
                </h3>
                <StatusBadge status={location.status} />
              </div>

              {location.address && (
                <p className="text-sm text-muted-foreground mt-1">
                  {location.address.line1}, {location.address.city} - {location.address.postalCode}
                </p>
              )}

              {location.contact?.phone && (
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground mt-1">
                  <Phone className="h-3.5 w-3.5" />
                  {location.contact.phone}
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onClick}>View Details</DropdownMenuItem>
              <DropdownMenuItem onClick={onEdit}>Edit Location</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onSchedule}>View Schedule</DropdownMenuItem>
              <DropdownMenuItem onClick={onManageStaff}>Manage Staff</DropdownMenuItem>
              <DropdownMenuItem onClick={onAnalytics}>View Analytics</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Departments */}
        {locationDepartments.length > 0 && (
          <div className="mt-4">
            <div className="flex flex-wrap gap-2">
              {locationDepartments.slice(0, 4).map((dept) => (
                <div
                  key={dept.id}
                  className="flex items-center gap-1.5 px-2 py-1 bg-muted rounded text-xs"
                >
                  <Stethoscope className="h-3 w-3 text-muted-foreground" />
                  <span>{dept.name}</span>
                </div>
              ))}
              {locationDepartments.length > 4 && (
                <Badge variant="outline" className="text-xs">
                  +{locationDepartments.length - 4} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-4 pt-4 border-t flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              {practitionerCount} doctors
            </span>
            <span className="flex items-center gap-1">
              <Stethoscope className="h-4 w-4" />
              {locationDepartments.length} depts
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onSchedule}>
              View Schedule
            </Button>
            <Button variant="outline" size="sm" onClick={onManageStaff}>
              Manage Staff
            </Button>
            <Button variant="ghost" size="sm" onClick={onAnalytics}>
              <BarChart3 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Organization Dashboard Component
// ============================================================================

interface OrganizationDashboardProps {
  organization: Organization;
  locations: Location[];
  departments: Department[];
  practitioners: Practitioner[];
  onLocationClick?: (location: Location) => void;
  onLocationSchedule?: (location: Location) => void;
  onLocationManageStaff?: (location: Location) => void;
  onLocationAnalytics?: (location: Location) => void;
  onLocationEdit?: (location: Location) => void;
  onAddLocation?: () => void;
  onEditOrganization?: () => void;
  className?: string;
}

export function OrganizationDashboard({
  organization,
  locations,
  departments,
  practitioners,
  onLocationClick,
  onLocationSchedule,
  onLocationManageStaff,
  onLocationAnalytics,
  onLocationEdit,
  onAddLocation,
  onEditOrganization,
  className,
}: OrganizationDashboardProps) {
  const getPractitionerCountForLocation = (locationId: string) =>
    practitioners.filter((p) => p.locationIds.includes(locationId)).length;

  return (
    <div className={cn("space-y-6", className)}>
      {/* Organization Header */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              {/* Organization Icon */}
              <div className="h-16 w-16 rounded-lg bg-primary/10 flex items-center justify-center">
                <Building className="h-8 w-8 text-primary" />
              </div>

              {/* Organization Info */}
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold">{organization.name}</h1>
                  <StatusBadge status={organization.status} />
                </div>
                <p className="text-muted-foreground capitalize">{organization.type}</p>

                {/* Quick Stats */}
                <div className="flex items-center gap-6 mt-4">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium">{locations.length} Locations</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium">{practitioners.length} Doctors</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Stethoscope className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium">{departments.length} Departments</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={onEditOrganization}>
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
              <Button onClick={onAddLocation}>
                <Plus className="h-4 w-4 mr-2" />
                Add Location
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Locations Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Locations</h2>
        </div>

        <div className="space-y-4">
          {locations.map((location) => (
            <LocationCard
              key={location.id}
              location={location}
              departments={departments}
              practitionerCount={getPractitionerCountForLocation(location.id)}
              onClick={() => onLocationClick?.(location)}
              onSchedule={() => onLocationSchedule?.(location)}
              onManageStaff={() => onLocationManageStaff?.(location)}
              onAnalytics={() => onLocationAnalytics?.(location)}
              onEdit={() => onLocationEdit?.(location)}
            />
          ))}

          {locations.length === 0 && (
            <Card className="border-dashed">
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Building className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-medium mb-2">No locations yet</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Add your first location to get started
                  </p>
                  <Button onClick={onAddLocation}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Location
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Department Card Component
// ============================================================================

interface DepartmentCardProps {
  department: Department;
  practitionerCount: number;
  onClick?: () => void;
  onEdit?: () => void;
  className?: string;
}

export function DepartmentCard({
  department,
  practitionerCount,
  onClick,
  onEdit,
  className,
}: DepartmentCardProps) {
  const getIconColor = () => {
    switch (department.color) {
      case "red":
        return "text-red-500 bg-red-500/10";
      case "blue":
        return "text-blue-500 bg-blue-500/10";
      case "green":
        return "text-green-500 bg-green-500/10";
      case "purple":
        return "text-purple-500 bg-purple-500/10";
      case "pink":
        return "text-pink-500 bg-pink-500/10";
      default:
        return "text-primary bg-primary/10";
    }
  };

  return (
    <Card
      className={cn("hover:shadow-md transition-shadow cursor-pointer", className)}
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", getIconColor())}>
              <Stethoscope className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-medium">{department.name}</h3>
              <p className="text-xs text-muted-foreground">{department.code}</p>
            </div>
          </div>
          <StatusBadge status={department.status} />
        </div>

        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="text-muted-foreground flex items-center gap-1">
            <Users className="h-4 w-4" />
            {practitionerCount} doctors
          </span>
          {department.appointmentSettings && (
            <span className="text-muted-foreground flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {department.appointmentSettings.defaultDuration}min slots
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Department List Component
// ============================================================================

interface DepartmentListProps {
  departments: Department[];
  practitioners: Practitioner[];
  onDepartmentClick?: (department: Department) => void;
  onAddDepartment?: () => void;
  className?: string;
}

export function DepartmentList({
  departments,
  practitioners,
  onDepartmentClick,
  onAddDepartment,
  className,
}: DepartmentListProps) {
  const getPractitionerCount = (departmentId: string) =>
    practitioners.filter((p) => p.departmentIds.includes(departmentId)).length;

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Departments</h2>
        {onAddDepartment && (
          <Button variant="outline" size="sm" onClick={onAddDepartment}>
            <Plus className="h-4 w-4 mr-2" />
            Add Department
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {departments.map((department) => (
          <DepartmentCard
            key={department.id}
            department={department}
            practitionerCount={getPractitionerCount(department.id)}
            onClick={() => onDepartmentClick?.(department)}
          />
        ))}

        {departments.length === 0 && (
          <Card className="col-span-full border-dashed">
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Stethoscope className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="font-medium mb-2">No departments yet</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Add departments to organize your practitioners
                </p>
                {onAddDepartment && (
                  <Button onClick={onAddDepartment}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Department
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default OrganizationDashboard;
