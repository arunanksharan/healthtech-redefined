'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Calendar as CalendarIcon,
  Clock,
  User,
  Plus,
  Filter,
  List,
  Grid,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Phone,
  CheckCircle2,
  AlertCircle,
  XCircle,
  CalendarDays,
  Stethoscope,
  Ban,
  UserCheck,
  ClipboardCheck,
  Trash2,
  Eye,
  MoreHorizontal,
  LogIn,
  UserX
} from 'lucide-react';
import { appointmentsAPI } from '@/lib/api/appointments';
import { patientsAPI } from '@/lib/api/patients';
import { practitionersAPI } from '@/lib/api/practitioners';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { MagicCard } from '@/components/ui/magic-card'; // Keep import but will replace usage
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { formatDate, formatSmartDate } from '@/lib/utils/date';
import { format, addDays, startOfWeek, endOfWeek, eachDayOfInterval, isSameDay, parseISO } from 'date-fns';
import { Skeleton, CalendarSkeleton, StatsCardSkeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';

type ViewMode = 'day' | 'week' | 'month' | 'list';

export default function AppointmentsPage() {
  const { toast } = useToast();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>('week');
  const [selectedAppointment, setSelectedAppointment] = useState<any>(null);
  const [isNewAppointmentOpen, setIsNewAppointmentOpen] = useState(false);
  const [appointmentForm, setAppointmentForm] = useState({
    patient_id: '',
    practitioner_id: '',
    appointment_date: format(new Date(), 'yyyy-MM-dd'),
    appointment_time: '09:00',
    appointment_type: 'consultation',
    reason_text: '',
    source_channel: 'web',
  });
  const queryClient = useQueryClient();

  // Fetch appointments
  const { data: appointmentsData, isLoading, isError, error } = useQuery({
    queryKey: ['appointments', currentDate, viewMode],
    queryFn: async () => {
      const [data, error] = await appointmentsAPI.getAll({
        start_date: format(currentDate, 'yyyy-MM-dd'),
        end_date: format(addDays(currentDate, viewMode === 'week' ? 7 : viewMode === 'day' ? 1 : 30), 'yyyy-MM-dd'),
      });
      if (error) throw new Error(error.message);
      return data;
    },
  });

  // Fetch appointment stats
  const { data: appointmentStats } = useQuery({
    queryKey: ['appointment-stats'],
    queryFn: async () => {
      const [data] = await appointmentsAPI.getStats();
      return data;
    },
    refetchInterval: 30000,
  });

  // Fetch patients for dropdown
  const { data: patientsData } = useQuery({
    queryKey: ['patients-list'],
    queryFn: async () => {
      const [data, error] = await patientsAPI.getAll({ page_size: 100 });
      if (error) throw new Error(error.message);
      return data;
    },
  });

  // Fetch practitioners for dropdown
  const { data: practitionersData } = useQuery({
    queryKey: ['practitioners-list'],
    queryFn: async () => {
      const [data, error] = await practitionersAPI.getAll({ page_size: 100 });
      if (error) throw new Error(error.message);
      return data;
    },
  });

  const patients = patientsData?.items || [];
  const practitioners = practitionersData?.items || [];

  // Create appointment mutation
  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const [result, error] = await appointmentsAPI.create(data);
      if (error) throw new Error(error.message);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      setIsNewAppointmentOpen(false);
      setAppointmentForm({
        patient_id: '',
        practitioner_id: '',
        appointment_date: format(new Date(), 'yyyy-MM-dd'),
        appointment_time: '09:00',
        appointment_type: 'consultation',
        reason_text: '',
        source_channel: 'web',
      });
      toast({ title: 'Success', description: 'Appointment created successfully!', variant: 'default' });
    },
    onError: (error: Error) => {
      toast({ title: 'Error', description: error.message || 'Failed to create appointment', variant: 'destructive' });
    },
  });

  // Confirm appointment mutation
  const confirmMutation = useMutation({
    mutationFn: async (id: string) => {
      const [result, error] = await appointmentsAPI.confirm(id);
      if (error) throw new Error(error.message);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      setSelectedAppointment(null);
      setSelectedAppointment(null);
      toast({ title: 'Success', description: 'Appointment confirmed!', variant: 'default' });
    },
    onError: (error: Error) => toast({ title: 'Error', description: error.message, variant: 'destructive' }),
  });

  // Check-in mutation
  const checkInMutation = useMutation({
    mutationFn: async (id: string) => {
      const [result, error] = await appointmentsAPI.checkIn(id);
      if (error) throw new Error(error.message);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      setSelectedAppointment(null);
      setSelectedAppointment(null);
      toast({ title: 'Success', description: 'Patient checked in!', variant: 'default' });
    },
    onError: (error: Error) => toast({ title: 'Error', description: error.message, variant: 'destructive' }),
  });

  // Complete appointment mutation
  const completeMutation = useMutation({
    mutationFn: async (id: string) => {
      const [result, error] = await appointmentsAPI.complete(id);
      if (error) throw new Error(error.message);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      setSelectedAppointment(null);
      setSelectedAppointment(null);
      toast({ title: 'Success', description: 'Appointment completed!', variant: 'default' });
    },
    onError: (error: Error) => toast({ title: 'Error', description: error.message, variant: 'destructive' }),
  });

  // Cancel appointment mutation
  const cancelMutation = useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      const [result, error] = await appointmentsAPI.cancel(id, reason);
      if (error) throw new Error(error.message);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      setSelectedAppointment(null);
      setSelectedAppointment(null);
      toast({ title: 'Success', description: 'Appointment cancelled', variant: 'default' });
    },
    onError: (error: Error) => toast({ title: 'Error', description: error.message, variant: 'destructive' }),
  });

  // Mark no-show mutation
  const noShowMutation = useMutation({
    mutationFn: async (id: string) => {
      const [result, error] = await appointmentsAPI.markNoShow(id);
      if (error) throw new Error(error.message);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      setSelectedAppointment(null);
      setSelectedAppointment(null);
      toast({ title: 'Success', description: 'Marked as no-show', variant: 'default' });
    },
    onError: (error: Error) => toast({ title: 'Error', description: error.message, variant: 'destructive' }),
  });

  // Delete appointment mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const [, error] = await appointmentsAPI.delete(id);
      if (error) throw new Error(error.message);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      setSelectedAppointment(null);
      setSelectedAppointment(null);
      toast({ title: 'Success', description: 'Appointment deleted', variant: 'default' });
    },
    onError: (error: Error) => toast({ title: 'Error', description: error.message, variant: 'destructive' }),
  });

  const handleNewAppointmentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!appointmentForm.patient_id || !appointmentForm.practitioner_id) {
      toast({ title: 'Validation Error', description: 'Please select both patient and practitioner', variant: 'destructive' });
      return;
    }
    createMutation.mutate(appointmentForm);
  };

  const appointments = appointmentsData?.items || [];
  const stats = {
    total: appointmentStats?.total || 0,
    confirmed: appointmentStats?.confirmed || 0,
    // pending includes requested, pending_confirm, and booked
    pending: (appointmentStats?.requested || 0) + (appointmentStats?.pending_confirm || 0) + (appointmentStats?.booked || 0),
    completed: appointmentStats?.completed || 0,
    cancelled: (appointmentStats?.cancelled || 0) + (appointmentStats?.no_show || 0),
    checkedIn: appointmentStats?.checked_in || 0,
    noShow: appointmentStats?.no_show || 0,
  };

  const navigateDate = (direction: 'prev' | 'next') => {
    const days = viewMode === 'day' ? 1 : viewMode === 'week' ? 7 : 30;
    setCurrentDate(prev => direction === 'next' ? addDays(prev, days) : addDays(prev, -days));
  };

  // Get status badge styling
  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      booked: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      confirmed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      pending: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      checked_in: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      completed: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
      cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      no_show: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
    };
    return styles[status] || styles.pending;
  };

  return (
    <div className="space-y-8 pb-10">
      {/* Flat Header */}
      <div className="flex items-center justify-between sticky top-[4rem] z-20 bg-white dark:bg-gray-900 py-4 -mx-6 px-6 border-b-2 border-gray-100 dark:border-gray-800">
        <div>
          <h1 className="text-2xl font-heading text-gray-900 dark:text-white">Appointments</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm">Manage and schedule your patient visits</p>
        </div>
        <Button
          onClick={() => setIsNewAppointmentOpen(true)}
          className="flat-btn-primary"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Appointment
        </Button>
      </div>

      {/* Flat Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Total</span>
            <CalendarIcon className="w-5 h-5 text-blue-500" />
          </div>
          <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.total}</div>
          <p className="text-xs text-gray-500 mt-1">All appointments</p>
        </div>

        <div className="bg-amber-50 dark:bg-amber-900/20 border-2 border-amber-200 dark:border-amber-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Pending</span>
            <AlertCircle className="w-5 h-5 text-amber-500" />
          </div>
          <div className="text-3xl font-bold text-amber-600 dark:text-amber-400">{stats.pending}</div>
          <p className="text-xs text-amber-600 mt-1">Needs action</p>
        </div>

        <div className="bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-200 dark:border-purple-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Checked In</span>
            <LogIn className="w-5 h-5 text-purple-500" />
          </div>
          <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">{stats.checkedIn}</div>
          <p className="text-xs text-purple-600 mt-1">In progress</p>
        </div>

        <div className="bg-emerald-50 dark:bg-emerald-900/20 border-2 border-emerald-200 dark:border-emerald-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Completed</span>
            <ClipboardCheck className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{stats.completed}</div>
          <p className="text-xs text-emerald-600 mt-1">Done</p>
        </div>

        <div className="bg-green-50 dark:bg-green-900/20 border-2 border-green-200 dark:border-green-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Confirmed</span>
            <CheckCircle2 className="w-5 h-5 text-green-500" />
          </div>
          <div className="text-3xl font-bold text-green-600 dark:text-green-400">{stats.confirmed}</div>
          <p className="text-xs text-green-600 mt-1">Ready</p>
        </div>

        <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Cancelled</span>
            <XCircle className="w-5 h-5 text-red-500" />
          </div>
          <div className="text-3xl font-bold text-red-600 dark:text-red-400">{stats.cancelled}</div>
          <p className="text-xs text-red-500 mt-1">{stats.noShow} no-shows</p>
        </div>
      </div>

      {/* Calendar Controls */}
      <div className="bg-white dark:bg-gray-800 p-2 rounded-lg border-2 border-gray-100 dark:border-gray-700 flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Date Navigation */}
        <div className="flex items-center gap-2 pl-2">
          <Button variant="ghost" size="icon" onClick={() => navigateDate('prev')} className="h-8 w-8 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
            <ChevronLeft className="w-5 h-5 text-gray-500" />
          </Button>
          <div className="text-base font-semibold min-w-[200px] text-center text-gray-900 dark:text-white">
            {viewMode === 'day' && format(currentDate, 'EEEE, MMMM d, yyyy')}
            {viewMode === 'week' && `${format(startOfWeek(currentDate), 'MMM d')} - ${format(endOfWeek(currentDate), 'MMM d, yyyy')}`}
            {viewMode === 'month' && format(currentDate, 'MMMM yyyy')}
            {viewMode === 'list' && 'All Appointments'}
          </div>
          <Button variant="ghost" size="icon" onClick={() => navigateDate('next')} className="h-8 w-8 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
            <ChevronRight className="w-5 h-5 text-gray-500" />
          </Button>
          <Button variant="outline" size="sm" onClick={() => setCurrentDate(new Date())} className="ml-2 h-8 text-xs font-medium border-2 border-gray-200 dark:border-gray-600">
            Today
          </Button>
        </div>

        {/* View Mode Toggle */}
        <div className="flex bg-gray-100 dark:bg-gray-700 p-1 rounded-lg border-2 border-gray-200 dark:border-gray-600">
          <button
            onClick={() => setViewMode('day')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${viewMode === 'day' ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white' : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'
              }`}
          >
            Day
          </button>
          <button
            onClick={() => setViewMode('week')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${viewMode === 'week' ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white' : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'
              }`}
          >
            Week
          </button>
          <button
            onClick={() => setViewMode('month')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${viewMode === 'month' ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white' : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'
              }`}
          >
            Month
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all flex items-center gap-1 ${viewMode === 'list' ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white' : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'
              }`}
          >
            <List className="w-4 h-4" />
            <span className="hidden sm:inline">List</span>
          </button>
        </div>

        <Button variant="outline" size="icon" className="h-9 w-9 border-2 border-gray-200 dark:border-gray-600 mr-2 text-gray-500">
          <Filter className="w-4 h-4" />
        </Button>
      </div>

      {/* Calendar/List View */}
      {isLoading ? (
        <CalendarSkeleton />
      ) : isError ? (
        <Alert variant="destructive" className="my-8">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error Loading Schedule</AlertTitle>
          <AlertDescription>
            {(error as Error)?.message || 'Failed to load appointments. Please try again.'}
          </AlertDescription>
        </Alert>
      ) : (
        <div className="animate-in fade-in duration-300">
          {viewMode === 'list' ? (
            <AppointmentsList appointments={appointments} onSelect={setSelectedAppointment} />
          ) : viewMode === 'week' ? (
            <WeekView appointments={appointments} currentDate={currentDate} onSelect={setSelectedAppointment} />
          ) : viewMode === 'day' ? (
            <DayView appointments={appointments} currentDate={currentDate} onSelect={setSelectedAppointment} />
          ) : (
            <MonthView appointments={appointments} currentDate={currentDate} onSelect={setSelectedAppointment} />
          )}
        </div>
      )}

      {/* New Appointment Dialog */}
      <Dialog open={isNewAppointmentOpen} onOpenChange={setIsNewAppointmentOpen}>
        <DialogContent className="sm:max-w-[550px] p-0 overflow-hidden rounded-lg border-2 border-gray-200 dark:border-gray-700">
          {/* Flat Header */}
          <div className="bg-blue-500 px-6 py-5 text-white">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white rounded-lg">
                <CalendarIcon className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <DialogTitle className="text-lg font-heading text-white">Schedule New Appointment</DialogTitle>
                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                  Book a new appointment for a patient with a practitioner
                </DialogDescription>
              </div>
            </div>
          </div>

          <form onSubmit={handleNewAppointmentSubmit} className="px-6 py-5">
            <div className="space-y-5">
              {/* Patient Selection */}
              <div className="space-y-2">
                <Label htmlFor="patient" className="text-sm font-medium text-foreground flex items-center gap-2">
                  <User className="h-3.5 w-3.5 text-muted-foreground" />
                  Patient <span className="text-red-500">*</span>
                </Label>
                <Select
                  value={appointmentForm.patient_id}
                  onValueChange={(value) => setAppointmentForm({ ...appointmentForm, patient_id: value })}
                >
                  <SelectTrigger className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background">
                    <SelectValue placeholder="Select a patient" />
                  </SelectTrigger>
                  <SelectContent>
                    {patients.map((patient: any) => (
                      <SelectItem key={patient.id} value={patient.id}>
                        {patient.legal_name || patient.name || `${patient.first_name || ''} ${patient.last_name || ''}`.trim()}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Practitioner Selection */}
              <div className="space-y-2">
                <Label htmlFor="practitioner" className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Stethoscope className="h-3.5 w-3.5 text-muted-foreground" />
                  Practitioner <span className="text-red-500">*</span>
                </Label>
                <Select
                  value={appointmentForm.practitioner_id}
                  onValueChange={(value) => setAppointmentForm({ ...appointmentForm, practitioner_id: value })}
                >
                  <SelectTrigger className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background">
                    <SelectValue placeholder="Select a practitioner" />
                  </SelectTrigger>
                  <SelectContent>
                    {practitioners.map((prac: any) => (
                      <SelectItem key={prac.id} value={prac.id}>
                        {prac.name || `${prac.first_name || ''} ${prac.last_name || ''}`.trim()}
                        {prac.speciality && ` (${prac.speciality})`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Date and Time */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="date" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <CalendarDays className="h-3.5 w-3.5 text-muted-foreground" />
                    Date <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="date"
                    type="date"
                    value={appointmentForm.appointment_date}
                    onChange={(e) => setAppointmentForm({ ...appointmentForm, appointment_date: e.target.value })}
                    min={format(new Date(), 'yyyy-MM-dd')}
                    className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="time" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                    Time <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="time"
                    type="time"
                    value={appointmentForm.appointment_time}
                    onChange={(e) => setAppointmentForm({ ...appointmentForm, appointment_time: e.target.value })}
                    className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                    required
                  />
                </div>
              </div>

              {/* Appointment Type */}
              <div className="space-y-2">
                <Label htmlFor="type" className="text-sm font-medium text-foreground flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-muted-foreground" />
                  Appointment Type
                </Label>
                <Select
                  value={appointmentForm.appointment_type}
                  onValueChange={(value) => setAppointmentForm({ ...appointmentForm, appointment_type: value })}
                >
                  <SelectTrigger className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="consultation">Consultation</SelectItem>
                    <SelectItem value="follow_up">Follow-up</SelectItem>
                    <SelectItem value="checkup">Checkup</SelectItem>
                    <SelectItem value="procedure">Procedure</SelectItem>
                    <SelectItem value="test">Test / Lab</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Reason */}
              <div className="space-y-2">
                <Label htmlFor="reason" className="text-sm font-medium text-foreground flex items-center gap-2">
                  <AlertCircle className="h-3.5 w-3.5 text-muted-foreground" />
                  Reason for Visit
                </Label>
                <Textarea
                  id="reason"
                  value={appointmentForm.reason_text}
                  onChange={(e) => setAppointmentForm({ ...appointmentForm, reason_text: e.target.value })}
                  placeholder="Brief description of the appointment reason..."
                  rows={3}
                  className="rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background resize-none"
                />
              </div>

              {/* Booking Source */}
              <div className="space-y-2">
                <Label htmlFor="source" className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                  Booking Source
                </Label>
                <Select
                  value={appointmentForm.source_channel}
                  onValueChange={(value) => setAppointmentForm({ ...appointmentForm, source_channel: value })}
                >
                  <SelectTrigger className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background">
                    <SelectValue placeholder="Select source" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="web">Web Portal</SelectItem>
                    <SelectItem value="phone">Phone Call</SelectItem>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                    <SelectItem value="voice_agent">Voice Agent</SelectItem>
                    <SelectItem value="walk_in">Walk-in</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 mt-6 pt-5 border-t border-border">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsNewAppointmentOpen(false)}
                className="rounded-full px-5 border-border hover:bg-muted"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending}
                className="rounded-full px-6 bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all"
              >
                {createMutation.isPending ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                    Scheduling...
                  </>
                ) : (
                  <>
                    <CalendarIcon className="w-4 h-4 mr-2" />
                    Schedule Appointment
                  </>
                )}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Appointment Detail Dialog */}
      <Dialog open={!!selectedAppointment} onOpenChange={() => setSelectedAppointment(null)}>
        <DialogContent className="sm:max-w-[550px] p-0 overflow-hidden rounded-2xl border-border">
          {selectedAppointment && (
            <>
              {/* Header with gradient based on status */}
              <div className={`px-6 py-5 text-white ${selectedAppointment.status === 'completed' ? 'bg-gradient-to-r from-emerald-600 to-teal-600' :
                selectedAppointment.status === 'cancelled' ? 'bg-gradient-to-r from-red-600 to-rose-600' :
                  selectedAppointment.status === 'checked_in' ? 'bg-gradient-to-r from-purple-600 to-violet-600' :
                    selectedAppointment.status === 'no_show' ? 'bg-gradient-to-r from-gray-600 to-slate-600' :
                      'bg-gradient-to-r from-blue-600 to-indigo-600'
                }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-white/20 rounded-xl">
                      <CalendarIcon className="h-5 w-5" />
                    </div>
                    <div>
                      <DialogTitle className="text-lg font-semibold text-white">Appointment Details</DialogTitle>
                      <DialogDescription className="text-white/80 text-sm mt-0.5">
                        {selectedAppointment.appointment_type || 'Consultation'} • {selectedAppointment.status?.replace('_', ' ').toUpperCase()}
                      </DialogDescription>
                    </div>
                  </div>
                  <Badge className={`${getStatusBadge(selectedAppointment.status)} font-medium`}>
                    {selectedAppointment.status?.replace('_', ' ')}
                  </Badge>
                </div>
              </div>

              <div className="px-6 py-5 space-y-5">
                {/* Patient Info */}
                <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
                  <Avatar className="h-12 w-12">
                    <AvatarFallback className="bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-400">
                      {selectedAppointment.patient_name?.charAt(0) || 'P'}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <p className="font-semibold text-foreground">{selectedAppointment.patient_name || 'Unknown Patient'}</p>
                    <p className="text-sm text-muted-foreground">Patient</p>
                  </div>
                </div>

                {/* Details Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                      <Stethoscope className="h-3.5 w-3.5" /> Practitioner
                    </p>
                    <p className="text-sm font-medium text-foreground">{selectedAppointment.practitioner_name || 'Not assigned'}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5" /> Location
                    </p>
                    <p className="text-sm font-medium text-foreground">{selectedAppointment.location_name || 'Main Clinic'}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                      <CalendarDays className="h-3.5 w-3.5" /> Date
                    </p>
                    <p className="text-sm font-medium text-foreground">
                      {selectedAppointment.scheduled_at ? format(parseISO(selectedAppointment.scheduled_at), 'EEEE, MMM d, yyyy') : 'Not scheduled'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5" /> Time
                    </p>
                    <p className="text-sm font-medium text-foreground">
                      {selectedAppointment.scheduled_at ? format(parseISO(selectedAppointment.scheduled_at), 'h:mm a') : '--:--'}
                    </p>
                  </div>
                </div>

                {/* Reason */}
                {selectedAppointment.reason_text && (
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Reason for Visit</p>
                    <p className="text-sm text-foreground bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg">{selectedAppointment.reason_text}</p>
                  </div>
                )}

                {/* Action Buttons based on status */}
                <div className="pt-4 border-t border-gray-100 dark:border-gray-800 space-y-3">
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Quick Actions</p>

                  <div className="flex flex-wrap gap-2">
                    {/* Confirm - for booked/pending */}
                    {['booked', 'pending'].includes(selectedAppointment.status) && (
                      <Button
                        size="sm"
                        onClick={() => confirmMutation.mutate(selectedAppointment.id)}
                        disabled={confirmMutation.isPending}
                        className="bg-green-600 hover:bg-green-700 text-white rounded-full"
                      >
                        <CheckCircle2 className="w-4 h-4 mr-1.5" />
                        Confirm
                      </Button>
                    )}

                    {/* Check In - for confirmed */}
                    {['confirmed', 'booked'].includes(selectedAppointment.status) && (
                      <Button
                        size="sm"
                        onClick={() => checkInMutation.mutate(selectedAppointment.id)}
                        disabled={checkInMutation.isPending}
                        className="bg-purple-600 hover:bg-purple-700 text-white rounded-full"
                      >
                        <LogIn className="w-4 h-4 mr-1.5" />
                        Check In
                      </Button>
                    )}

                    {/* Complete - for checked_in */}
                    {selectedAppointment.status === 'checked_in' && (
                      <Button
                        size="sm"
                        onClick={() => completeMutation.mutate(selectedAppointment.id)}
                        disabled={completeMutation.isPending}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-full"
                      >
                        <ClipboardCheck className="w-4 h-4 mr-1.5" />
                        Complete
                      </Button>
                    )}

                    {/* No Show - for booked/confirmed/checked_in */}
                    {['booked', 'confirmed', 'checked_in'].includes(selectedAppointment.status) && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => noShowMutation.mutate(selectedAppointment.id)}
                        disabled={noShowMutation.isPending}
                        className="rounded-full border-border"
                      >
                        <UserX className="w-4 h-4 mr-1.5" />
                        No Show
                      </Button>
                    )}

                    {/* Cancel - for non-completed/cancelled */}
                    {!['completed', 'cancelled', 'no_show'].includes(selectedAppointment.status) && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => cancelMutation.mutate({ id: selectedAppointment.id })}
                        disabled={cancelMutation.isPending}
                        className="rounded-full border-red-200 dark:border-red-900 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950"
                      >
                        <Ban className="w-4 h-4 mr-1.5" />
                        Cancel
                      </Button>
                    )}

                    {/* Delete - always available */}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        if (confirm('Are you sure you want to delete this appointment?')) {
                          deleteMutation.mutate(selectedAppointment.id);
                        }
                      }}
                      disabled={deleteMutation.isPending}
                      className="rounded-full border-red-200 dark:border-red-900 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950"
                    >
                      <Trash2 className="w-4 h-4 mr-1.5" />
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function AppointmentsList({ appointments, onSelect }: { appointments: any[]; onSelect: (apt: any) => void }) {
  return (
    <Card className="border-border shadow-sm overflow-hidden">
      <div className="bg-background px-6 py-3 border-b border-border">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          {appointments.length} Appointments Found
        </h3>
      </div>
      <CardContent className="p-0">
        <div className="divide-y divide-border/50">
          {appointments.map((appointment) => (
            <div
              key={appointment.id}
              onClick={() => onSelect(appointment)}
              className="group flex items-center justify-between p-4 hover:bg-accent/50 cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className={`w-1.5 h-12 rounded-full ${appointment.status === 'confirmed' ? 'bg-green-500' :
                  appointment.status === 'pending' ? 'bg-yellow-500' :
                    appointment.status === 'cancelled' ? 'bg-red-500' :
                      'bg-muted'
                  }`} />

                <div className="min-w-[120px]">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="font-semibold text-foreground">
                      {formatSmartDate(appointment.scheduled_at)}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground ml-6 flex items-center gap-1">
                    <CalendarDays className="w-3 h-3" />
                    {format(parseISO(appointment.scheduled_at), 'MMM d, yyyy')}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10 border border-border">
                    <AvatarImage src={appointment.patient?.avatar_url} />
                    <AvatarFallback className="bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 text-xs font-bold">
                      {appointment.patient?.name?.substring(0, 2).toUpperCase() || 'P'}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium text-foreground">
                      {appointment.patient?.name || 'Unknown Patient'}
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {appointment.practitioner?.name || 'No practitioner'}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Badge variant="outline" className="border-border text-muted-foreground font-normal">
                  {appointment.appointment_type || 'General'}
                </Badge>
                <Badge
                  variant={
                    appointment.status === 'confirmed' ? 'success' :
                      appointment.status === 'pending' ? 'warning' :
                        appointment.status === 'cancelled' ? 'destructive' : 'secondary'
                  }
                  className={`capitalize ${appointment.status === 'confirmed' ? 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800' :
                    appointment.status === 'pending' ? 'bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800' :
                      appointment.status === 'cancelled' ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800' :
                        'bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700'
                    }`}
                >
                  {appointment.status}
                </Badge>
                <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-blue-400 transition-colors" />
              </div>
            </div>
          ))}

          {appointments.length === 0 && (
            <div className="text-center py-16">
              <div className="bg-muted w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <CalendarIcon className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium text-foreground">No appointments found</h3>
              <p className="text-muted-foreground mt-1">Try selecting a different date/view or create a new one.</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function WeekView({ appointments, currentDate, onSelect }: { appointments: any[]; currentDate: Date; onSelect: (apt: any) => void }) {
  const weekStart = startOfWeek(currentDate);
  const weekEnd = endOfWeek(currentDate);
  const weekDays = eachDayOfInterval({ start: weekStart, end: weekEnd });

  const getAppointmentsForDay = (day: Date) => {
    return appointments.filter(apt =>
      isSameDay(parseISO(apt.scheduled_at), day)
    );
  };

  return (
    <Card className="border-border shadow-sm overflow-hidden">
      <CardContent className="p-0">
        <div className="grid grid-cols-7 divide-x divide-border">
          {weekDays.map((day) => {
            const dayAppointments = getAppointmentsForDay(day);
            const isToday = isSameDay(day, new Date());

            return (
              <div key={day.toString()} className="min-h-[500px] flex flex-col group">
                <div className={`text-center py-3 border-b border-border ${isToday ? 'bg-blue-50/50 dark:bg-blue-900/10' : 'bg-muted/30'
                  }`}>
                  <div className={`text-xs font-semibold uppercase ${isToday ? 'text-blue-600 dark:text-blue-400' : 'text-muted-foreground'}`}>
                    {format(day, 'EEE')}
                  </div>
                  <div className={`text-xl font-bold mt-1 ${isToday
                    ? 'bg-blue-600 text-white w-8 h-8 flex items-center justify-center rounded-full mx-auto shadow-sm'
                    : 'text-foreground'
                    }`}>
                    {format(day, 'd')}
                  </div>
                </div>

                <div className={`flex-1 p-2 space-y-2 transition-colors ${isToday ? 'bg-blue-50/10 dark:bg-blue-900/5' : 'group-hover:bg-accent/20'}`}>
                  {dayAppointments.map((apt) => (
                    <div
                      key={apt.id}
                      onClick={() => onSelect(apt)}
                      className={`p-2 rounded-md border text-xs cursor-pointer shadow-sm hover:shadow-md transition-all ${apt.status === 'confirmed' ? 'border-green-200 bg-green-50/80 hover:bg-green-100 dark:border-green-900 dark:bg-green-900/20 dark:hover:bg-green-900/40' :
                        apt.status === 'pending' ? 'border-yellow-200 bg-yellow-50/80 hover:bg-yellow-100 dark:border-yellow-900 dark:bg-yellow-900/20 dark:hover:bg-yellow-900/40' :
                          'border-red-200 bg-red-50/80 hover:bg-red-100 dark:border-red-900 dark:bg-red-900/20 dark:hover:bg-red-900/40'
                        }`}
                    >
                      <div className="font-semibold text-foreground mb-1">
                        {format(parseISO(apt.scheduled_at), 'h:mm a')}
                      </div>
                      <div className="font-medium text-foreground truncate">
                        {apt.patient?.name}
                      </div>
                      <div className="text-muted-foreground truncate mt-0.5">
                        {apt.appointment_type}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function DayView({ appointments, currentDate, onSelect }: { appointments: any[]; currentDate: Date; onSelect: (apt: any) => void }) {
  const dayAppointments = appointments.filter(apt =>
    isSameDay(parseISO(apt.scheduled_at), currentDate)
  ).sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime());

  const hours = Array.from({ length: 13 }, (_, i) => i + 8); // 8 AM to 8 PM

  return (
    <Card className="border-border shadow-sm overflow-hidden">
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {hours.map((hour) => {
            const hourAppointments = dayAppointments.filter(apt => {
              const aptHour = new Date(apt.scheduled_at).getHours();
              return aptHour === hour;
            });

            return (
              <div key={hour} className="flex min-h-[100px] group hover:bg-accent/30 transition-colors">
                <div className="w-20 border-r border-border p-4 text-xs font-semibold text-muted-foreground text-right">
                  {format(new Date().setHours(hour, 0), 'h:mm a')}
                </div>
                <div className="flex-1 p-2 relative">
                  {/* Hour grid line */}
                  <div className="absolute top-0 left-0 right-0 h-px bg-border/50" />

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 mt-1">
                    {hourAppointments.map((apt) => (
                      <div
                        key={apt.id}
                        onClick={() => onSelect(apt)}
                        className={`p-3 rounded-lg border-l-4 cursor-pointer shadow-sm hover:translate-y-[-1px] transition-all bg-card ${apt.status === 'confirmed' ? 'border-green-500' :
                          apt.status === 'pending' ? 'border-yellow-500' :
                            'border-red-500'
                          }`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <span className="text-xs font-bold text-foreground bg-accent px-1.5 py-0.5 rounded">
                            {format(parseISO(apt.scheduled_at), 'h:mm a')}
                          </span>
                          <Badge variant={apt.status === 'confirmed' ? 'success' : apt.status === 'pending' ? 'warning' : 'destructive'} className="text-[10px] h-5 px-1.5">
                            {apt.status}
                          </Badge>
                        </div>
                        <div className="font-semibold text-sm text-foreground line-clamp-1">{apt.patient?.name}</div>
                        <div className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
                          <User className="w-3 h-3" />
                          <span className="line-clamp-1">{apt.practitioner?.name}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function MonthView({ appointments, currentDate, onSelect }: { appointments: any[]; currentDate: Date; onSelect: (apt: any) => void }) {
  // Enhanced Month View (Placeholder for full calendar grid, currently defaulting to List for better usability)
  // In a real app, this would be a full big-calendar implementation
  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-100 dark:bg-blue-900/20 dark:border-blue-900/50 text-blue-800 dark:text-blue-300 px-4 py-3 rounded-lg text-sm flex items-center">
        <CalendarIcon className="w-4 h-4 mr-2" />
        Showing list view for the selected month
      </div>
      <AppointmentsList appointments={appointments} onSelect={onSelect} />
    </div>
  );
}

