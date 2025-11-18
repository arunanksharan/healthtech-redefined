'use client';

import { use } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Phone,
  Mail,
  MapPin,
  Calendar,
  User,
  Activity,
  MessageSquare,
  FileText,
  Clock,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { patientsAPI } from '@/lib/api/patients';
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

export default function Patient360Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  // Fetch patient 360 view
  const { data: view, isLoading, error } = useQuery({
    queryKey: ['patient-360', id],
    queryFn: async () => {
      const [data, error] = await patientsAPI.get360View(id);
      if (error) throw new Error(error.message);
      return data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !view) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">
          Error loading patient: {(error as Error)?.message}
        </p>
        <Link href="/dashboard/patients">
          <Button className="mt-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Patients
          </Button>
        </Link>
      </div>
    );
  }

  const { patient, appointments, journeys, communications, tickets } = view;

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link href="/dashboard/patients">
        <Button variant="ghost">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Patients
        </Button>
      </Link>

      {/* Patient Header */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-6">
              <Avatar className="w-24 h-24">
                <AvatarImage src={patient.avatar_url} />
                <AvatarFallback className="text-2xl">
                  {patient.name
                    .split(' ')
                    .map((n) => n[0])
                    .join('')
                    .toUpperCase()}
                </AvatarFallback>
              </Avatar>

              <div className="space-y-3">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">
                    {patient.name}
                  </h1>
                  <p className="text-gray-500 mt-1">
                    MRN: <code className="text-xs bg-gray-100 px-2 py-1 rounded">{patient.mrn}</code>
                  </p>
                </div>

                <div className="flex items-center gap-4 text-sm text-gray-600">
                  {patient.phone && (
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4" />
                      {patient.phone}
                    </div>
                  )}
                  {patient.email && (
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4" />
                      {patient.email}
                    </div>
                  )}
                  {patient.date_of_birth && (
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      {formatDate(patient.date_of_birth, 'MMM d, yyyy')}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      patient.status === 'active'
                        ? 'success'
                        : patient.status === 'inactive'
                        ? 'secondary'
                        : 'warning'
                    }
                  >
                    {patient.status || 'Unknown'}
                  </Badge>
                  {patient.gender && (
                    <Badge variant="outline">{patient.gender}</Badge>
                  )}
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button variant="outline">Edit Profile</Button>
              <Button>Book Appointment</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Appointments</CardDescription>
              <Calendar className="w-4 h-4 text-blue-600" />
            </div>
            <CardTitle className="text-3xl">
              {appointments?.length || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Active Journeys</CardDescription>
              <Activity className="w-4 h-4 text-green-600" />
            </div>
            <CardTitle className="text-3xl">
              {journeys?.length || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Communications</CardDescription>
              <MessageSquare className="w-4 h-4 text-purple-600" />
            </div>
            <CardTitle className="text-3xl">
              {communications?.length || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardDescription>Open Tickets</CardDescription>
              <FileText className="w-4 h-4 text-yellow-600" />
            </div>
            <CardTitle className="text-3xl">
              {tickets?.length || 0}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Appointments */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Appointments</CardTitle>
            <CardDescription>Latest appointment history</CardDescription>
          </CardHeader>
          <CardContent>
            {appointments && appointments.length > 0 ? (
              <div className="space-y-4">
                {appointments.slice(0, 5).map((appointment) => (
                  <div
                    key={appointment.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <Calendar className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <div className="font-medium text-sm">
                          {appointment.appointment_type || 'Consultation'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {formatSmartDate(appointment.scheduled_at)}
                        </div>
                      </div>
                    </div>
                    <Badge variant={
                      appointment.status === 'completed' ? 'success' :
                      appointment.status === 'cancelled' ? 'destructive' :
                      'default'
                    }>
                      {appointment.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">
                No appointments found
              </p>
            )}
          </CardContent>
        </Card>

        {/* Active Journeys */}
        <Card>
          <CardHeader>
            <CardTitle>Active Journeys</CardTitle>
            <CardDescription>Ongoing care journeys</CardDescription>
          </CardHeader>
          <CardContent>
            {journeys && journeys.length > 0 ? (
              <div className="space-y-4">
                {journeys.slice(0, 5).map((journey) => (
                  <div
                    key={journey.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                        <Activity className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <div className="font-medium text-sm">
                          {journey.journey_type || 'Care Journey'}
                        </div>
                        <div className="text-xs text-gray-500">
                          Started {formatSmartDate(journey.created_at)}
                        </div>
                      </div>
                    </div>
                    <Badge variant={
                      journey.status === 'completed' ? 'success' :
                      journey.status === 'cancelled' ? 'destructive' :
                      'default'
                    }>
                      {journey.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">
                No active journeys
              </p>
            )}
          </CardContent>
        </Card>

        {/* Recent Communications */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Communications</CardTitle>
            <CardDescription>Latest messages and notifications</CardDescription>
          </CardHeader>
          <CardContent>
            {communications && communications.length > 0 ? (
              <div className="space-y-4">
                {communications.slice(0, 5).map((comm) => (
                  <div
                    key={comm.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                        <MessageSquare className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <div className="font-medium text-sm">
                          {comm.type || 'Message'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {formatSmartDate(comm.sent_at)}
                        </div>
                      </div>
                    </div>
                    <Badge variant={
                      comm.status === 'delivered' ? 'success' :
                      comm.status === 'failed' ? 'destructive' :
                      'default'
                    }>
                      {comm.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">
                No communications found
              </p>
            )}
          </CardContent>
        </Card>

        {/* Open Tickets */}
        <Card>
          <CardHeader>
            <CardTitle>Open Tickets</CardTitle>
            <CardDescription>Support tickets and issues</CardDescription>
          </CardHeader>
          <CardContent>
            {tickets && tickets.length > 0 ? (
              <div className="space-y-4">
                {tickets.slice(0, 5).map((ticket) => (
                  <div
                    key={ticket.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                        <FileText className="w-5 h-5 text-yellow-600" />
                      </div>
                      <div>
                        <div className="font-medium text-sm">
                          {ticket.title || 'Support Ticket'}
                        </div>
                        <div className="text-xs text-gray-500">
                          Created {formatSmartDate(ticket.created_at)}
                        </div>
                      </div>
                    </div>
                    <Badge variant={
                      ticket.status === 'resolved' ? 'success' :
                      ticket.status === 'closed' ? 'secondary' :
                      ticket.priority === 'high' ? 'destructive' :
                      'warning'
                    }>
                      {ticket.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">
                No open tickets
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
