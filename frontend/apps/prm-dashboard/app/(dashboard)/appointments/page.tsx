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

  const appointments = appointmentsData?.items || [];
  const stats = {
    total: appointments.length,
    confirmed: appointments.filter(a => a.status === 'confirmed').length,
    pending: appointments.filter(a => a.status === 'scheduled').length,
    cancelled: appointments.filter(a => a.status === 'cancelled').length,
  };

  const navigateDate = (direction: 'prev' | 'next') => {
    const days = viewMode === 'day' ? 1 : viewMode === 'week' ? 7 : 30;
    setCurrentDate(prev => direction === 'next' ? addDays(prev, days) : addDays(prev, -days));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'success';
      case 'pending': return 'warning';
      case 'cancelled': return 'destructive';
      case 'completed': return 'secondary';
      default: return 'default';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'consultation': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'follow_up': return 'bg-green-100 text-green-700 border-green-200';
      case 'procedure': return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'test': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Appointments</h1>
          <p className="text-gray-500 mt-1">Manage and schedule appointments</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Appointment
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Total Appointments</CardDescription>
            <CardTitle className="text-3xl">{stats.total}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Confirmed</CardDescription>
            <CardTitle className="text-3xl text-green-600">{stats.confirmed}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Pending</CardDescription>
            <CardTitle className="text-3xl text-yellow-600">{stats.pending}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Cancelled</CardDescription>
            <CardTitle className="text-3xl text-red-600">{stats.cancelled}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Calendar Controls */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {/* View Mode Toggle */}
            <div className="flex items-center gap-2">
              <Button
                variant={viewMode === 'day' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('day')}
              >
                Day
              </Button>
              <Button
                variant={viewMode === 'week' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('week')}
              >
                Week
              </Button>
              <Button
                variant={viewMode === 'month' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('month')}
              >
                Month
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('list')}
              >
                <List className="w-4 h-4" />
              </Button>
            </div>

            {/* Date Navigation */}
            <div className="flex items-center gap-4">
              <Button variant="outline" size="sm" onClick={() => navigateDate('prev')}>
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <div className="text-lg font-semibold min-w-[200px] text-center">
                {viewMode === 'day' && format(currentDate, 'EEEE, MMMM d, yyyy')}
                {viewMode === 'week' && `${format(startOfWeek(currentDate), 'MMM d')} - ${format(endOfWeek(currentDate), 'MMM d, yyyy')}`}
                {viewMode === 'month' && format(currentDate, 'MMMM yyyy')}
                {viewMode === 'list' && 'All Appointments'}
              </div>
              <Button variant="outline" size="sm" onClick={() => navigateDate('next')}>
                <ChevronRight className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={() => setCurrentDate(new Date())}>
                Today
              </Button>
            </div>

            {/* Filter Button */}
            <Button variant="outline" size="sm">
              <Filter className="w-4 h-4 mr-2" />
              Filter
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Calendar/List View */}
      {isLoading ? (
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          </CardContent>
        </Card>
      ) : viewMode === 'list' ? (
        <AppointmentsList appointments={appointments} onSelect={setSelectedAppointment} />
      ) : viewMode === 'week' ? (
        <WeekView appointments={appointments} currentDate={currentDate} onSelect={setSelectedAppointment} />
      ) : viewMode === 'day' ? (
        <DayView appointments={appointments} currentDate={currentDate} onSelect={setSelectedAppointment} />
      ) : (
        <MonthView appointments={appointments} currentDate={currentDate} onSelect={setSelectedAppointment} />
      )}
    </div>
  );
}

function AppointmentsList({ appointments, onSelect }: { appointments: any[]; onSelect: (apt: any) => void }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>All Appointments</CardTitle>
        <CardDescription>{appointments.length} total appointments</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {appointments.map((appointment) => (
            <div
              key={appointment.id}
              onClick={() => onSelect(appointment)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className={`w-1 h-16 rounded-full ${
                  appointment.status === 'confirmed' ? 'bg-green-500' :
                  appointment.status === 'pending' ? 'bg-yellow-500' :
                  appointment.status === 'cancelled' ? 'bg-red-500' :
                  'bg-gray-400'
                }`} />

                <div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span className="font-medium">
                      {formatSmartDate(appointment.scheduled_at)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <User className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-600">
                      {appointment.patient?.name || 'Unknown Patient'}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {appointment.practitioner?.name || 'No practitioner assigned'}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Badge variant={appointment.status === 'confirmed' ? 'success' : appointment.status === 'pending' ? 'warning' : 'destructive'}>
                  {appointment.status}
                </Badge>
                <Badge variant="outline">
                  {appointment.appointment_type || 'General'}
                </Badge>
              </div>
            </div>
          ))}

          {appointments.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <CalendarIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No appointments found</p>
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
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-7 gap-4">
          {weekDays.map((day) => {
            const dayAppointments = getAppointmentsForDay(day);
            const isToday = isSameDay(day, new Date());

            return (
              <div key={day.toString()} className="min-h-[300px]">
                <div className={`text-center p-2 rounded-lg mb-2 ${
                  isToday ? 'bg-blue-600 text-white' : 'bg-gray-100'
                }`}>
                  <div className="text-xs font-medium">{format(day, 'EEE')}</div>
                  <div className="text-lg font-bold">{format(day, 'd')}</div>
                </div>

                <div className="space-y-2">
                  {dayAppointments.map((apt) => (
                    <div
                      key={apt.id}
                      onClick={() => onSelect(apt)}
                      className={`p-2 rounded-lg border-l-4 cursor-pointer hover:shadow-md transition-shadow ${
                        apt.status === 'confirmed' ? 'border-green-500 bg-green-50' :
                        apt.status === 'pending' ? 'border-yellow-500 bg-yellow-50' :
                        'border-red-500 bg-red-50'
                      }`}
                    >
                      <div className="text-xs font-medium">
                        {format(parseISO(apt.scheduled_at), 'h:mm a')}
                      </div>
                      <div className="text-xs text-gray-600 truncate">
                        {apt.patient?.name}
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

  const hours = Array.from({ length: 12 }, (_, i) => i + 8); // 8 AM to 8 PM

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-1">
          {hours.map((hour) => {
            const hourAppointments = dayAppointments.filter(apt => {
              const aptHour = new Date(apt.scheduled_at).getHours();
              return aptHour === hour;
            });

            return (
              <div key={hour} className="flex gap-4 border-b border-gray-100 py-3">
                <div className="w-20 text-sm font-medium text-gray-500">
                  {format(new Date().setHours(hour, 0), 'h:mm a')}
                </div>
                <div className="flex-1 space-y-2">
                  {hourAppointments.map((apt) => (
                    <div
                      key={apt.id}
                      onClick={() => onSelect(apt)}
                      className={`p-3 rounded-lg border-l-4 cursor-pointer hover:shadow-md transition-shadow ${
                        apt.status === 'confirmed' ? 'border-green-500 bg-green-50' :
                        apt.status === 'pending' ? 'border-yellow-500 bg-yellow-50' :
                        'border-red-500 bg-red-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{apt.patient?.name}</div>
                          <div className="text-sm text-gray-600">
                            {apt.practitioner?.name} • {apt.appointment_type}
                          </div>
                        </div>
                        <Badge variant={apt.status === 'confirmed' ? 'success' : apt.status === 'pending' ? 'warning' : 'destructive'}>
                          {apt.status}
                        </Badge>
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

function MonthView({ appointments, currentDate, onSelect }: { appointments: any[]; currentDate: Date; onSelect: (apt: any) => void }) {
  // Simplified month view - can be enhanced with a proper calendar grid
  return <AppointmentsList appointments={appointments} onSelect={onSelect} />;
}
