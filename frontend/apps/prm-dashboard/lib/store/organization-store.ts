"use client";

import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";

// ============================================================================
// Types & Interfaces
// ============================================================================

export type EntityStatus = "active" | "inactive" | "pending" | "suspended";
export type PractitionerStatus = "active" | "inactive" | "on_leave" | "pending";
export type SlotStatus = "free" | "busy" | "busy-unavailable" | "busy-tentative";
export type AppointmentStatus = "booked" | "pending" | "arrived" | "fulfilled" | "cancelled" | "noshow";

export interface Address {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

export interface ContactInfo {
  phone?: string;
  email?: string;
  fax?: string;
  website?: string;
}

export interface OperatingHours {
  dayOfWeek: number; // 0-6 (Sunday-Saturday)
  allDay: boolean;
  openingTime?: string; // HH:mm format
  closingTime?: string;
}

// Organization
export interface Organization {
  id: string;
  name: string;
  type: "hospital" | "clinic" | "lab" | "pharmacy" | "network";
  status: EntityStatus;
  address?: Address;
  contact?: ContactInfo;
  partOf?: string; // Parent organization ID
  alias?: string[];
  createdAt: Date;
  updatedAt: Date;
}

// Location
export interface Location {
  id: string;
  name: string;
  organizationId: string;
  status: EntityStatus;
  mode: "instance" | "kind";
  type: "building" | "wing" | "floor" | "room" | "virtual";
  address?: Address;
  contact?: ContactInfo;
  operatingHours: OperatingHours[];
  description?: string;
  photo?: string;
  createdAt: Date;
  updatedAt: Date;
}

// Department
export interface Department {
  id: string;
  name: string;
  code: string;
  locationId: string;
  organizationId: string;
  status: EntityStatus;
  icon?: string;
  color?: string;
  headPractitionerId?: string;
  operatingHours: OperatingHours[];
  appointmentSettings?: {
    defaultDuration: number; // minutes
    bufferTime: number;
    maxDailyBookings: number;
    bookingLeadTime: number;
    cancellationNotice: number; // hours
  };
  createdAt: Date;
  updatedAt: Date;
}

// Practitioner
export interface Practitioner {
  id: string;
  name: string;
  firstName: string;
  lastName: string;
  prefix?: string; // Dr., Prof., etc.
  suffix?: string; // MD, PhD, etc.
  qualifications: string[];
  specialties: string[];
  photo?: string;
  gender?: "male" | "female" | "other" | "unknown";
  contact?: ContactInfo;
  status: PractitionerStatus;
  leaveStart?: Date;
  leaveEnd?: Date;
  locationIds: string[];
  departmentIds: string[];
  organizationId: string;
  bio?: string;
  languages?: string[];
  rating?: number;
  totalAppointments?: number;
  noShowRate?: number;
  createdAt: Date;
  updatedAt: Date;
}

// Schedule
export interface Schedule {
  id: string;
  practitionerId: string;
  locationId: string;
  departmentId: string;
  serviceType?: string;
  planningHorizon: {
    start: Date;
    end: Date;
  };
  comment?: string;
  active: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Slot
export interface Slot {
  id: string;
  scheduleId: string;
  practitionerId: string;
  locationId?: string;
  departmentId?: string;
  start: Date;
  end: Date;
  status: SlotStatus;
  serviceType?: string;
  specialty?: string;
  appointmentType?: string;
  comment?: string;
  overbooked?: boolean;
  recurringId?: string; // For recurring slots
  createdAt: Date;
  updatedAt: Date;
}

// Appointment (simplified for this context)
export interface Appointment {
  id: string;
  slotId?: string;
  patientId: string;
  patientName: string;
  practitionerId: string;
  practitionerName: string;
  locationId: string;
  departmentId?: string;
  start: Date;
  end: Date;
  status: AppointmentStatus;
  appointmentType?: string;
  reason?: string;
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
}

// Filter types
export interface EntityFilters {
  search: string;
  status: EntityStatus | "all";
  locationId: string | "all";
  departmentId: string | "all";
  sortBy: string;
  sortOrder: "asc" | "desc";
}

export interface SlotFilters {
  practitionerId: string | "all";
  departmentId: string | "all";
  status: SlotStatus | "all";
  dateRange: { start: Date; end: Date };
}

// ============================================================================
// State Interface
// ============================================================================

export interface OrganizationState {
  // Organizations
  organizations: Organization[];
  selectedOrganization: Organization | null;
  isLoadingOrganizations: boolean;

  // Locations
  locations: Location[];
  selectedLocation: Location | null;
  isLoadingLocations: boolean;

  // Departments
  departments: Department[];
  selectedDepartment: Department | null;
  isLoadingDepartments: boolean;

  // Practitioners
  practitioners: Practitioner[];
  selectedPractitioner: Practitioner | null;
  isLoadingPractitioners: boolean;
  practitionerFilters: EntityFilters;

  // Schedules & Slots
  schedules: Schedule[];
  slots: Slot[];
  isLoadingSchedules: boolean;
  slotFilters: SlotFilters;

  // Appointments
  appointments: Appointment[];
  isLoadingAppointments: boolean;

  // UI State
  quickViewOpen: boolean;
  quickViewEntity: { type: "patient" | "practitioner" | "location"; id: string } | null;
  calendarView: "day" | "week" | "month";
  calendarDate: Date;
}

// ============================================================================
// Actions Interface
// ============================================================================

export interface OrganizationActions {
  // Organization actions
  setOrganizations: (orgs: Organization[]) => void;
  selectOrganization: (org: Organization | null) => void;
  loadOrganizations: () => Promise<void>;
  createOrganization: (org: Partial<Organization>) => Promise<void>;
  updateOrganization: (id: string, updates: Partial<Organization>) => Promise<void>;

  // Location actions
  setLocations: (locations: Location[]) => void;
  selectLocation: (location: Location | null) => void;
  loadLocations: (organizationId?: string) => Promise<void>;
  createLocation: (location: Partial<Location>) => Promise<void>;
  updateLocation: (id: string, updates: Partial<Location>) => Promise<void>;

  // Department actions
  setDepartments: (departments: Department[]) => void;
  selectDepartment: (department: Department | null) => void;
  loadDepartments: (locationId?: string) => Promise<void>;
  createDepartment: (department: Partial<Department>) => Promise<void>;
  updateDepartment: (id: string, updates: Partial<Department>) => Promise<void>;

  // Practitioner actions
  setPractitioners: (practitioners: Practitioner[]) => void;
  selectPractitioner: (practitioner: Practitioner | null) => void;
  loadPractitioners: (filters?: Partial<EntityFilters>) => Promise<void>;
  createPractitioner: (practitioner: Partial<Practitioner>) => Promise<void>;
  updatePractitioner: (id: string, updates: Partial<Practitioner>) => Promise<void>;
  setPractitionerFilters: (filters: Partial<EntityFilters>) => void;

  // Schedule & Slot actions
  setSchedules: (schedules: Schedule[]) => void;
  setSlots: (slots: Slot[]) => void;
  loadSlots: (filters?: Partial<SlotFilters>) => Promise<void>;
  createSlot: (slot: Partial<Slot>) => Promise<void>;
  updateSlot: (id: string, updates: Partial<Slot>) => Promise<void>;
  deleteSlot: (id: string) => Promise<void>;
  setSlotFilters: (filters: Partial<SlotFilters>) => void;

  // Appointment actions
  setAppointments: (appointments: Appointment[]) => void;
  loadAppointments: (dateRange: { start: Date; end: Date }) => Promise<void>;

  // UI actions
  openQuickView: (type: "patient" | "practitioner" | "location", id: string) => void;
  closeQuickView: () => void;
  setCalendarView: (view: "day" | "week" | "month") => void;
  setCalendarDate: (date: Date) => void;

  // Reset
  reset: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState: OrganizationState = {
  organizations: [],
  selectedOrganization: null,
  isLoadingOrganizations: false,

  locations: [],
  selectedLocation: null,
  isLoadingLocations: false,

  departments: [],
  selectedDepartment: null,
  isLoadingDepartments: false,

  practitioners: [],
  selectedPractitioner: null,
  isLoadingPractitioners: false,
  practitionerFilters: {
    search: "",
    status: "all",
    locationId: "all",
    departmentId: "all",
    sortBy: "name",
    sortOrder: "asc",
  },

  schedules: [],
  slots: [],
  isLoadingSchedules: false,
  slotFilters: {
    practitionerId: "all",
    departmentId: "all",
    status: "all",
    dateRange: {
      start: new Date(),
      end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    },
  },

  appointments: [],
  isLoadingAppointments: false,

  quickViewOpen: false,
  quickViewEntity: null,
  calendarView: "week",
  calendarDate: new Date(),
};

// ============================================================================
// Store
// ============================================================================

export const useOrganizationStore = create<OrganizationState & OrganizationActions>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // ========================================================================
      // Organization Actions
      // ========================================================================

      setOrganizations: (organizations) => {
        set({ organizations });
      },

      selectOrganization: (org) => {
        set({ selectedOrganization: org });
      },

      loadOrganizations: async () => {
        set({ isLoadingOrganizations: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));
          const mockOrgs = createMockOrganizations();
          set({ organizations: mockOrgs, isLoadingOrganizations: false });
        } catch {
          set({ isLoadingOrganizations: false });
        }
      },

      createOrganization: async (org) => {
        const { organizations } = get();
        const newOrg: Organization = {
          id: `org-${Date.now()}`,
          name: org.name || "New Organization",
          type: org.type || "clinic",
          status: "pending",
          address: org.address,
          contact: org.contact,
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        set({ organizations: [...organizations, newOrg] });
      },

      updateOrganization: async (id, updates) => {
        const { organizations } = get();
        set({
          organizations: organizations.map((org) =>
            org.id === id ? { ...org, ...updates, updatedAt: new Date() } : org
          ),
        });
      },

      // ========================================================================
      // Location Actions
      // ========================================================================

      setLocations: (locations) => {
        set({ locations });
      },

      selectLocation: (location) => {
        set({ selectedLocation: location });
      },

      loadLocations: async (organizationId) => {
        set({ isLoadingLocations: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));
          const mockLocations = createMockLocations(organizationId);
          set({ locations: mockLocations, isLoadingLocations: false });
        } catch {
          set({ isLoadingLocations: false });
        }
      },

      createLocation: async (location) => {
        const { locations } = get();
        const newLocation: Location = {
          id: `loc-${Date.now()}`,
          name: location.name || "New Location",
          organizationId: location.organizationId || "org-1",
          status: "pending",
          mode: "instance",
          type: "building",
          operatingHours: [],
          createdAt: new Date(),
          updatedAt: new Date(),
          ...location,
        };
        set({ locations: [...locations, newLocation] });
      },

      updateLocation: async (id, updates) => {
        const { locations } = get();
        set({
          locations: locations.map((loc) =>
            loc.id === id ? { ...loc, ...updates, updatedAt: new Date() } : loc
          ),
        });
      },

      // ========================================================================
      // Department Actions
      // ========================================================================

      setDepartments: (departments) => {
        set({ departments });
      },

      selectDepartment: (department) => {
        set({ selectedDepartment: department });
      },

      loadDepartments: async (locationId) => {
        set({ isLoadingDepartments: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));
          const mockDepts = createMockDepartments(locationId);
          set({ departments: mockDepts, isLoadingDepartments: false });
        } catch {
          set({ isLoadingDepartments: false });
        }
      },

      createDepartment: async (department) => {
        const { departments } = get();
        const newDept: Department = {
          id: `dept-${Date.now()}`,
          name: department.name || "New Department",
          code: department.code || "NEW",
          locationId: department.locationId || "loc-1",
          organizationId: department.organizationId || "org-1",
          status: "pending",
          operatingHours: [],
          createdAt: new Date(),
          updatedAt: new Date(),
          ...department,
        };
        set({ departments: [...departments, newDept] });
      },

      updateDepartment: async (id, updates) => {
        const { departments } = get();
        set({
          departments: departments.map((dept) =>
            dept.id === id ? { ...dept, ...updates, updatedAt: new Date() } : dept
          ),
        });
      },

      // ========================================================================
      // Practitioner Actions
      // ========================================================================

      setPractitioners: (practitioners) => {
        set({ practitioners });
      },

      selectPractitioner: (practitioner) => {
        set({ selectedPractitioner: practitioner });
      },

      loadPractitioners: async (filters) => {
        set({ isLoadingPractitioners: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));
          const mockPractitioners = createMockPractitioners();
          set({ practitioners: mockPractitioners, isLoadingPractitioners: false });
        } catch {
          set({ isLoadingPractitioners: false });
        }
      },

      createPractitioner: async (practitioner) => {
        const { practitioners } = get();
        const newPractitioner: Practitioner = {
          id: `prac-${Date.now()}`,
          name: `${practitioner.firstName || ""} ${practitioner.lastName || ""}`.trim() || "New Practitioner",
          firstName: practitioner.firstName || "",
          lastName: practitioner.lastName || "",
          qualifications: practitioner.qualifications || [],
          specialties: practitioner.specialties || [],
          status: "pending",
          locationIds: practitioner.locationIds || [],
          departmentIds: practitioner.departmentIds || [],
          organizationId: practitioner.organizationId || "org-1",
          createdAt: new Date(),
          updatedAt: new Date(),
          ...practitioner,
        };
        set({ practitioners: [...practitioners, newPractitioner] });
      },

      updatePractitioner: async (id, updates) => {
        const { practitioners } = get();
        set({
          practitioners: practitioners.map((prac) =>
            prac.id === id ? { ...prac, ...updates, updatedAt: new Date() } : prac
          ),
        });
      },

      setPractitionerFilters: (filters) => {
        const { practitionerFilters } = get();
        set({ practitionerFilters: { ...practitionerFilters, ...filters } });
      },

      // ========================================================================
      // Schedule & Slot Actions
      // ========================================================================

      setSchedules: (schedules) => {
        set({ schedules });
      },

      setSlots: (slots) => {
        set({ slots });
      },

      loadSlots: async (filters) => {
        set({ isLoadingSchedules: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));
          const mockSlots = createMockSlots();
          set({ slots: mockSlots, isLoadingSchedules: false });
        } catch {
          set({ isLoadingSchedules: false });
        }
      },

      createSlot: async (slot) => {
        const { slots } = get();
        const newSlot: Slot = {
          id: `slot-${Date.now()}`,
          scheduleId: slot.scheduleId || "schedule-1",
          practitionerId: slot.practitionerId || "prac-1",
          start: slot.start || new Date(),
          end: slot.end || new Date(Date.now() + 60 * 60 * 1000),
          status: "free",
          createdAt: new Date(),
          updatedAt: new Date(),
          ...slot,
        };
        set({ slots: [...slots, newSlot] });
      },

      updateSlot: async (id, updates) => {
        const { slots } = get();
        set({
          slots: slots.map((slot) =>
            slot.id === id ? { ...slot, ...updates, updatedAt: new Date() } : slot
          ),
        });
      },

      deleteSlot: async (id) => {
        const { slots } = get();
        set({ slots: slots.filter((slot) => slot.id !== id) });
      },

      setSlotFilters: (filters) => {
        const { slotFilters } = get();
        set({ slotFilters: { ...slotFilters, ...filters } });
      },

      // ========================================================================
      // Appointment Actions
      // ========================================================================

      setAppointments: (appointments) => {
        set({ appointments });
      },

      loadAppointments: async (dateRange) => {
        set({ isLoadingAppointments: true });
        try {
          await new Promise((resolve) => setTimeout(resolve, 500));
          const mockAppointments = createMockAppointments();
          set({ appointments: mockAppointments, isLoadingAppointments: false });
        } catch {
          set({ isLoadingAppointments: false });
        }
      },

      // ========================================================================
      // UI Actions
      // ========================================================================

      openQuickView: (type, id) => {
        set({ quickViewOpen: true, quickViewEntity: { type, id } });
      },

      closeQuickView: () => {
        set({ quickViewOpen: false, quickViewEntity: null });
      },

      setCalendarView: (view) => {
        set({ calendarView: view });
      },

      setCalendarDate: (date) => {
        set({ calendarDate: date });
      },

      // ========================================================================
      // Reset
      // ========================================================================

      reset: () => {
        set(initialState);
      },
    })),
    { name: "organization-store" }
  )
);

// ============================================================================
// Mock Data Generators
// ============================================================================

function createMockOrganizations(): Organization[] {
  return [
    {
      id: "org-1",
      name: "Surya Hospitals",
      type: "network",
      status: "active",
      address: {
        line1: "Corporate Office",
        city: "Bangalore",
        state: "Karnataka",
        postalCode: "560001",
        country: "India",
      },
      contact: {
        phone: "+91 80 1234 5678",
        email: "info@suryahospitals.com",
        website: "https://suryahospitals.com",
      },
      createdAt: new Date("2020-01-01"),
      updatedAt: new Date(),
    },
  ];
}

function createMockLocations(organizationId?: string): Location[] {
  return [
    {
      id: "loc-1",
      name: "Surya Whitefield",
      organizationId: organizationId || "org-1",
      status: "active",
      mode: "instance",
      type: "building",
      address: {
        line1: "123 Main Street",
        city: "Whitefield",
        state: "Karnataka",
        postalCode: "560066",
        country: "India",
      },
      contact: {
        phone: "+91 80 1234 5678",
        email: "whitefield@suryahospitals.com",
      },
      operatingHours: [
        { dayOfWeek: 1, allDay: false, openingTime: "09:00", closingTime: "21:00" },
        { dayOfWeek: 2, allDay: false, openingTime: "09:00", closingTime: "21:00" },
        { dayOfWeek: 3, allDay: false, openingTime: "09:00", closingTime: "21:00" },
        { dayOfWeek: 4, allDay: false, openingTime: "09:00", closingTime: "21:00" },
        { dayOfWeek: 5, allDay: false, openingTime: "09:00", closingTime: "21:00" },
        { dayOfWeek: 6, allDay: false, openingTime: "09:00", closingTime: "13:00" },
      ],
      createdAt: new Date("2020-01-15"),
      updatedAt: new Date(),
    },
    {
      id: "loc-2",
      name: "Surya Indiranagar",
      organizationId: organizationId || "org-1",
      status: "active",
      mode: "instance",
      type: "building",
      address: {
        line1: "45 CMH Road",
        city: "Indiranagar",
        state: "Karnataka",
        postalCode: "560038",
        country: "India",
      },
      contact: {
        phone: "+91 80 8765 4321",
        email: "indiranagar@suryahospitals.com",
      },
      operatingHours: [
        { dayOfWeek: 1, allDay: false, openingTime: "09:00", closingTime: "21:00" },
        { dayOfWeek: 2, allDay: false, openingTime: "09:00", closingTime: "21:00" },
        { dayOfWeek: 3, allDay: false, openingTime: "09:00", closingTime: "21:00" },
        { dayOfWeek: 4, allDay: false, openingTime: "09:00", closingTime: "21:00" },
        { dayOfWeek: 5, allDay: false, openingTime: "09:00", closingTime: "21:00" },
        { dayOfWeek: 6, allDay: false, openingTime: "09:00", closingTime: "13:00" },
      ],
      createdAt: new Date("2021-03-01"),
      updatedAt: new Date(),
    },
    {
      id: "loc-3",
      name: "Surya Electronic City",
      organizationId: organizationId || "org-1",
      status: "pending",
      mode: "instance",
      type: "building",
      address: {
        line1: "Phase 1",
        city: "Electronic City",
        state: "Karnataka",
        postalCode: "560100",
        country: "India",
      },
      operatingHours: [],
      description: "Coming Soon",
      createdAt: new Date(),
      updatedAt: new Date(),
    },
  ];
}

function createMockDepartments(locationId?: string): Department[] {
  const departments: Department[] = [
    {
      id: "dept-1",
      name: "Cardiology",
      code: "CARD",
      locationId: locationId || "loc-1",
      organizationId: "org-1",
      status: "active",
      icon: "heart",
      color: "red",
      headPractitionerId: "prac-1",
      operatingHours: [
        { dayOfWeek: 1, allDay: false, openingTime: "09:00", closingTime: "18:00" },
        { dayOfWeek: 2, allDay: false, openingTime: "09:00", closingTime: "18:00" },
        { dayOfWeek: 3, allDay: false, openingTime: "09:00", closingTime: "18:00" },
        { dayOfWeek: 4, allDay: false, openingTime: "09:00", closingTime: "18:00" },
        { dayOfWeek: 5, allDay: false, openingTime: "09:00", closingTime: "18:00" },
      ],
      appointmentSettings: {
        defaultDuration: 30,
        bufferTime: 5,
        maxDailyBookings: 20,
        bookingLeadTime: 60,
        cancellationNotice: 24,
      },
      createdAt: new Date("2020-01-15"),
      updatedAt: new Date(),
    },
    {
      id: "dept-2",
      name: "Orthopedics",
      code: "ORTHO",
      locationId: locationId || "loc-1",
      organizationId: "org-1",
      status: "active",
      icon: "bone",
      color: "blue",
      headPractitionerId: "prac-2",
      operatingHours: [
        { dayOfWeek: 1, allDay: false, openingTime: "09:00", closingTime: "18:00" },
        { dayOfWeek: 2, allDay: false, openingTime: "09:00", closingTime: "18:00" },
        { dayOfWeek: 3, allDay: false, openingTime: "09:00", closingTime: "18:00" },
        { dayOfWeek: 4, allDay: false, openingTime: "09:00", closingTime: "18:00" },
        { dayOfWeek: 5, allDay: false, openingTime: "09:00", closingTime: "18:00" },
      ],
      appointmentSettings: {
        defaultDuration: 30,
        bufferTime: 5,
        maxDailyBookings: 15,
        bookingLeadTime: 60,
        cancellationNotice: 24,
      },
      createdAt: new Date("2020-01-15"),
      updatedAt: new Date(),
    },
    {
      id: "dept-3",
      name: "General Medicine",
      code: "GEN",
      locationId: locationId || "loc-1",
      organizationId: "org-1",
      status: "active",
      icon: "stethoscope",
      color: "green",
      operatingHours: [
        { dayOfWeek: 1, allDay: false, openingTime: "08:00", closingTime: "20:00" },
        { dayOfWeek: 2, allDay: false, openingTime: "08:00", closingTime: "20:00" },
        { dayOfWeek: 3, allDay: false, openingTime: "08:00", closingTime: "20:00" },
        { dayOfWeek: 4, allDay: false, openingTime: "08:00", closingTime: "20:00" },
        { dayOfWeek: 5, allDay: false, openingTime: "08:00", closingTime: "20:00" },
        { dayOfWeek: 6, allDay: false, openingTime: "08:00", closingTime: "14:00" },
      ],
      appointmentSettings: {
        defaultDuration: 20,
        bufferTime: 5,
        maxDailyBookings: 30,
        bookingLeadTime: 30,
        cancellationNotice: 12,
      },
      createdAt: new Date("2020-01-15"),
      updatedAt: new Date(),
    },
    {
      id: "dept-4",
      name: "Pediatrics",
      code: "PED",
      locationId: locationId || "loc-1",
      organizationId: "org-1",
      status: "active",
      icon: "baby",
      color: "pink",
      operatingHours: [
        { dayOfWeek: 1, allDay: false, openingTime: "09:00", closingTime: "17:00" },
        { dayOfWeek: 2, allDay: false, openingTime: "09:00", closingTime: "17:00" },
        { dayOfWeek: 3, allDay: false, openingTime: "09:00", closingTime: "17:00" },
        { dayOfWeek: 4, allDay: false, openingTime: "09:00", closingTime: "17:00" },
        { dayOfWeek: 5, allDay: false, openingTime: "09:00", closingTime: "17:00" },
      ],
      appointmentSettings: {
        defaultDuration: 20,
        bufferTime: 5,
        maxDailyBookings: 25,
        bookingLeadTime: 30,
        cancellationNotice: 12,
      },
      createdAt: new Date("2020-01-15"),
      updatedAt: new Date(),
    },
  ];

  return departments;
}

function createMockPractitioners(): Practitioner[] {
  return [
    {
      id: "prac-1",
      name: "Dr. Rohit Sharma",
      firstName: "Rohit",
      lastName: "Sharma",
      prefix: "Dr.",
      suffix: "MD, DM",
      qualifications: ["MBBS", "MD (Internal Medicine)", "DM (Cardiology)"],
      specialties: ["Cardiology", "Interventional Cardiology"],
      gender: "male",
      contact: {
        phone: "+91 98765 43210",
        email: "rohit.sharma@suryahospitals.com",
      },
      status: "active",
      locationIds: ["loc-1"],
      departmentIds: ["dept-1"],
      organizationId: "org-1",
      bio: "Dr. Rohit Sharma is a renowned cardiologist with over 15 years of experience in interventional cardiology.",
      languages: ["English", "Hindi", "Kannada"],
      rating: 4.8,
      totalAppointments: 142,
      noShowRate: 8.5,
      createdAt: new Date("2020-02-01"),
      updatedAt: new Date(),
    },
    {
      id: "prac-2",
      name: "Dr. Virat Kohli",
      firstName: "Virat",
      lastName: "Kohli",
      prefix: "Dr.",
      suffix: "MS",
      qualifications: ["MBBS", "MS (Orthopedics)"],
      specialties: ["Orthopedics", "Sports Medicine"],
      gender: "male",
      contact: {
        phone: "+91 98765 43211",
        email: "virat.kohli@suryahospitals.com",
      },
      status: "active",
      locationIds: ["loc-1"],
      departmentIds: ["dept-2"],
      organizationId: "org-1",
      bio: "Dr. Virat Kohli specializes in sports injuries and joint replacement surgeries.",
      languages: ["English", "Hindi"],
      rating: 4.9,
      totalAppointments: 128,
      noShowRate: 5.2,
      createdAt: new Date("2020-03-15"),
      updatedAt: new Date(),
    },
    {
      id: "prac-3",
      name: "Dr. Priya Mehta",
      firstName: "Priya",
      lastName: "Mehta",
      prefix: "Dr.",
      suffix: "MD",
      qualifications: ["MBBS", "MD (Endocrinology)"],
      specialties: ["Endocrinology", "Diabetes Management"],
      gender: "female",
      contact: {
        phone: "+91 98765 43212",
        email: "priya.mehta@suryahospitals.com",
      },
      status: "active",
      locationIds: ["loc-2"],
      departmentIds: ["dept-3"],
      organizationId: "org-1",
      bio: "Dr. Priya Mehta is an experienced endocrinologist specializing in diabetes and thyroid disorders.",
      languages: ["English", "Hindi", "Gujarati"],
      rating: 4.7,
      totalAppointments: 156,
      noShowRate: 6.8,
      createdAt: new Date("2021-01-10"),
      updatedAt: new Date(),
    },
    {
      id: "prac-4",
      name: "Dr. Amit Patel",
      firstName: "Amit",
      lastName: "Patel",
      prefix: "Dr.",
      qualifications: ["MBBS"],
      specialties: ["General Medicine"],
      gender: "male",
      contact: {
        phone: "+91 98765 43213",
        email: "amit.patel@suryahospitals.com",
      },
      status: "on_leave",
      leaveStart: new Date("2024-12-01"),
      leaveEnd: new Date("2024-12-05"),
      locationIds: ["loc-1", "loc-2"],
      departmentIds: ["dept-3"],
      organizationId: "org-1",
      languages: ["English", "Hindi", "Marathi"],
      rating: 4.5,
      totalAppointments: 89,
      noShowRate: 10.2,
      createdAt: new Date("2022-06-01"),
      updatedAt: new Date(),
    },
  ];
}

function createMockSlots(): Slot[] {
  const now = new Date();
  const slots: Slot[] = [];

  // Generate slots for the current week
  for (let day = 0; day < 7; day++) {
    const date = new Date(now);
    date.setDate(date.getDate() + day);

    // Skip weekends for most doctors
    if (date.getDay() === 0 || date.getDay() === 6) continue;

    // Morning slots
    const morningStart = new Date(date);
    morningStart.setHours(9, 0, 0, 0);
    const morningEnd = new Date(date);
    morningEnd.setHours(13, 0, 0, 0);

    slots.push({
      id: `slot-${day}-morning-1`,
      scheduleId: "schedule-1",
      practitionerId: "prac-1",
      locationId: "loc-1",
      departmentId: "dept-1",
      start: morningStart,
      end: morningEnd,
      status: day === 0 ? "busy" : "free",
      serviceType: "consultation",
      specialty: "Cardiology",
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    // Evening slots
    const eveningStart = new Date(date);
    eveningStart.setHours(14, 0, 0, 0);
    const eveningEnd = new Date(date);
    eveningEnd.setHours(18, 0, 0, 0);

    if (day % 2 === 0) {
      slots.push({
        id: `slot-${day}-evening-1`,
        scheduleId: "schedule-1",
        practitionerId: "prac-1",
        locationId: "loc-1",
        departmentId: "dept-1",
        start: eveningStart,
        end: eveningEnd,
        status: "free",
        serviceType: "consultation",
        specialty: "Cardiology",
        createdAt: new Date(),
        updatedAt: new Date(),
      });
    }
  }

  return slots;
}

function createMockAppointments(): Appointment[] {
  const now = new Date();
  return [
    {
      id: "appt-1",
      patientId: "patient-1",
      patientName: "John Doe",
      practitionerId: "prac-1",
      practitionerName: "Dr. Rohit Sharma",
      locationId: "loc-1",
      departmentId: "dept-1",
      start: new Date(now.setHours(10, 0, 0, 0)),
      end: new Date(now.setHours(10, 30, 0, 0)),
      status: "booked",
      appointmentType: "Follow-up",
      reason: "Cardiology check-up",
      createdAt: new Date(),
      updatedAt: new Date(),
    },
    {
      id: "appt-2",
      patientId: "patient-2",
      patientName: "Jane Smith",
      practitionerId: "prac-1",
      practitionerName: "Dr. Rohit Sharma",
      locationId: "loc-1",
      departmentId: "dept-1",
      start: new Date(now.setHours(11, 0, 0, 0)),
      end: new Date(now.setHours(11, 30, 0, 0)),
      status: "booked",
      appointmentType: "Consultation",
      reason: "Chest pain evaluation",
      createdAt: new Date(),
      updatedAt: new Date(),
    },
    {
      id: "appt-3",
      patientId: "patient-3",
      patientName: "Bob Johnson",
      practitionerId: "prac-2",
      practitionerName: "Dr. Virat Kohli",
      locationId: "loc-1",
      departmentId: "dept-2",
      start: new Date(now.setHours(14, 0, 0, 0)),
      end: new Date(now.setHours(14, 30, 0, 0)),
      status: "pending",
      appointmentType: "New Patient",
      reason: "Knee pain",
      createdAt: new Date(),
      updatedAt: new Date(),
    },
  ];
}

// ============================================================================
// Selectors
// ============================================================================

export const selectOrganizations = (state: OrganizationState) => state.organizations;
export const selectLocations = (state: OrganizationState) => state.locations;
export const selectDepartments = (state: OrganizationState) => state.departments;
export const selectPractitioners = (state: OrganizationState) => state.practitioners;
export const selectSlots = (state: OrganizationState) => state.slots;
export const selectAppointments = (state: OrganizationState) => state.appointments;

export const selectLocationsByOrg = (state: OrganizationState, orgId: string) =>
  state.locations.filter((loc) => loc.organizationId === orgId);

export const selectDepartmentsByLocation = (state: OrganizationState, locationId: string) =>
  state.departments.filter((dept) => dept.locationId === locationId);

export const selectPractitionersByDepartment = (state: OrganizationState, departmentId: string) =>
  state.practitioners.filter((prac) => prac.departmentIds.includes(departmentId));

export const selectSlotsByPractitioner = (state: OrganizationState, practitionerId: string) =>
  state.slots.filter((slot) => slot.practitionerId === practitionerId);
