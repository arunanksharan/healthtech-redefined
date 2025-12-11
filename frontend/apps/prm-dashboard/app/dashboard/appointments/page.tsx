'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
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
  CalendarDays
} from 'lucide-react';
import { appointmentsAPI } from '@/lib/api/appointments';
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
import { MagicCard } from '@/components/ui/magic-card';
import { formatDate, formatSmartDate } from '@/lib/utils/date';
import { format, addDays, startOfWeek, endOfWeek, eachDayOfInterval, isSameDay, parseISO } from 'date-fns';
import toast from 'react-hot-toast';

type ViewMode = 'day' | 'week' | 'month' | 'list';

export default function AppointmentsPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>('week');
  const [selectedAppointment, setSelectedAppointment] = useState<any>(null);

  // Fetch appointments
  const { data: appointmentsData, isLoading } = useQuery({
    queryKey: ['appointments', currentDate, viewMode],
    queryFn: async () => {
      const [data, error] = await appointmentsAPI.getAll({
        date_start: format(currentDate, 'yyyy-MM-dd'),
        date_end: format(addDays(currentDate, viewMode === 'week' ? 7 : viewMode === 'day' ? 1 : 30), 'yyyy-MM-dd'),
      });
      if (error) throw new Error(error.message);
      return data;
    },
  });

  const appointments = appointmentsData?.data || [];
  const stats = {
    total: appointments.length,
    confirmed: appointments.filter(a => a.status === 'confirmed').length,
    pending: appointments.filter(a => a.status === 'pending').length,
    cancelled: appointments.filter(a => a.status === 'cancelled').length,
  };

  const navigateDate = (direction: 'prev' | 'next') => {
    const days = viewMode === 'day' ? 1 : viewMode === 'week' ? 7 : 30;
    setCurrentDate(prev => direction === 'next' ? addDays(prev, days) : addDays(prev, -days));
  };

  return (
    <div className="space-y-8 pb-10">
      {/* Sticky Header */}
      <div className="flex items-center justify-between sticky top-[4rem] z-20 bg-background/90 backdrop-blur-md py-4 -mx-6 px-6 border-b border-border/50">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Appointments</h1>
          <p className="text-muted-foreground text-sm">Manage and schedule your patient visits</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all rounded-full px-6">
          <Plus className="w-4 h-4 mr-2" />
          New Appointment
        </Button>
      </div>

      {/* Magic Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--info) / 0.2)">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Appointments</CardTitle>
            <CalendarIcon className="w-4 h-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{stats.total}</div>
            <p className="text-xs text-muted-foreground mt-1">For the selected period</p>
          </CardContent>
        </MagicCard>

        <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--success) / 0.2)">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Confirmed</CardTitle>
            <CheckCircle2 className="w-4 h-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{stats.confirmed}</div>
            <p className="text-xs text-green-600 mt-1 font-medium">Ready to visit</p>
          </CardContent>
        </MagicCard>

        <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--warning) / 0.2)">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pending</CardTitle>
            <AlertCircle className="w-4 h-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{stats.pending}</div>
            <p className="text-xs text-amber-600 mt-1 font-medium">Needs confirmation</p>
          </CardContent>
        </MagicCard>

        <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--destructive) / 0.2)">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Cancelled</CardTitle>
            <XCircle className="w-4 h-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{stats.cancelled}</div>
            <p className="text-xs text-red-500 mt-1 font-medium">Reschedule required</p>
          </CardContent>
        </MagicCard>
      </div>

      {/* Calendar Controls */}
      <div className="bg-card p-2 rounded-xl border border-border shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Date Navigation */}
        <div className="flex items-center gap-2 pl-2">
          <Button variant="ghost" size="icon" onClick={() => navigateDate('prev')} className="h-8 w-8 hover:bg-accent rounded-full">
            <ChevronLeft className="w-5 h-5 text-muted-foreground" />
          </Button>
          <div className="text-base font-semibold min-w-[200px] text-center text-foreground">
            {viewMode === 'day' && format(currentDate, 'EEEE, MMMM d, yyyy')}
            {viewMode === 'week' && `${format(startOfWeek(currentDate), 'MMM d')} - ${format(endOfWeek(currentDate), 'MMM d, yyyy')}`}
            {viewMode === 'month' && format(currentDate, 'MMMM yyyy')}
            {viewMode === 'list' && 'All Appointments'}
          </div>
          <Button variant="ghost" size="icon" onClick={() => navigateDate('next')} className="h-8 w-8 hover:bg-accent rounded-full">
            <ChevronRight className="w-5 h-5 text-muted-foreground" />
          </Button>
          <Button variant="outline" size="sm" onClick={() => setCurrentDate(new Date())} className="ml-2 h-8 text-xs font-medium border-border">
            Today
          </Button>
        </div>

        {/* View Mode Toggle */}
        <div className="flex bg-muted/50 p-1 rounded-lg border border-border/50">
          <button
            onClick={() => setViewMode('day')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${viewMode === 'day' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
          >
            Day
          </button>
          <button
            onClick={() => setViewMode('week')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${viewMode === 'week' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
          >
            Week
          </button>
          <button
            onClick={() => setViewMode('month')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${viewMode === 'month' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
          >
            Month
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all flex items-center gap-1 ${viewMode === 'list' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
          >
            <List className="w-4 h-4" />
            <span className="hidden sm:inline">List</span>
          </button>
        </div>

        <Button variant="outline" size="icon" className="h-9 w-9 border-border mr-2 text-muted-foreground">
          <Filter className="w-4 h-4" />
        </Button>
      </div>

      {/* Calendar/List View */}
      {isLoading ? (
        <Card className="border-border shadow-sm min-h-[400px]">
          <CardContent className="py-20">
            <div className="flex flex-col items-center justify-center">
              <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-muted-foreground text-sm">Loading schedule...</p>
            </div>
          </CardContent>
        </Card>
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
    </div>
  );
}

function AppointmentsList({ appointments, onSelect }: { appointments: any[]; onSelect: (apt: any) => void }) {
  return (
    <Card className="border-border shadow-sm overflow-hidden">
      <div className="bg-muted/50 px-6 py-3 border-b border-border">
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
