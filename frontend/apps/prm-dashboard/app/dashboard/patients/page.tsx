'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Search, Plus, User, Phone, Mail, Eye, Edit, MoreVertical, Activity, Users, Clock, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { patientsAPI } from '@/lib/api/patients';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { MagicCard } from '@/components/ui/magic-card';
import { formatDate } from '@/lib/utils/date';
import toast from 'react-hot-toast';

export default function PatientsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<'name' | 'phone' | 'mrn'>('name');

  // Fetch all patients
  const { data: patientsData, isLoading, error } = useQuery({
    queryKey: ['patients'],
    queryFn: async () => {
      const [data, error] = await patientsAPI.getAll();
      if (error) throw new Error(error.message);
      return data;
    },
  });

  // Search patients
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast.error('Please enter a search term');
      return;
    }

    const [results, error] = await patientsAPI.search(searchQuery, searchType);

    if (error) {
      toast.error('Search failed: ' + error.message);
      return;
    }

    toast.success(`Found ${results?.length || 0} patients`);
  };

  const patients = patientsData?.data || [];
  const totalCount = patientsData?.total || 0;

  return (
    <div className="space-y-8 pb-10">
      {/* Sticky Header */}
      <div className="flex items-center justify-between sticky top-[4rem] z-20 bg-gray-50/90 backdrop-blur-md py-4 -mx-6 px-6 border-b border-gray-200/50">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Patients</h1>
          <p className="text-gray-500 text-sm">
            Manage your patient directory and records
          </p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all rounded-full px-6">
          <Plus className="w-4 h-4 mr-2" />
          Add Patient
        </Button>
      </div>

      {/* Magic Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#eff6ff">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-gray-500">Total Patients</CardTitle>
            <Users className="w-4 h-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{totalCount}</div>
            <p className="text-xs text-gray-500 mt-1">+12% from last month</p>
          </CardContent>
        </MagicCard>

        <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#f0fdf4">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-gray-500">Active</CardTitle>
            <Activity className="w-4 h-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">
              {patients.filter((p) => p.status === 'active').length}
            </div>
            <p className="text-xs text-green-600 mt-1 font-medium">98% adherence rate</p>
          </CardContent>
        </MagicCard>

        <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#eff6ff">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-gray-500">New This Month</CardTitle>
            <User className="w-4 h-4 text-indigo-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">12</div>
            <p className="text-xs text-gray-500 mt-1">4 pending intake</p>
          </CardContent>
        </MagicCard>

        <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#fefce8">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-gray-500">Pending Follow-up</CardTitle>
            <AlertCircle className="w-4 h-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">3</div>
            <p className="text-xs text-amber-600 mt-1 font-medium">Action required</p>
          </CardContent>
        </MagicCard>
      </div>

      {/* Search & Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col sm:flex-row sm:items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search by name, MRN, or phone..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="pl-10 border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
          />
        </div>
        <div className="flex items-center gap-3">
          <select
            value={searchType}
            onChange={(e) => setSearchType(e.target.value as any)}
            className="h-10 px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-100 bg-gray-50/50"
          >
            <option value="name">Name</option>
            <option value="phone">Phone</option>
            <option value="mrn">MRN</option>
          </select>
          <Button onClick={handleSearch} variant="outline" className="h-10 border-gray-200 hover:bg-gray-50 text-gray-700">
            Search
          </Button>
        </div>
      </div>

      {/* Patients Table */}
      <Card className="border-gray-200 shadow-sm overflow-hidden">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-gray-500 text-sm">Loading patient records...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-600 bg-red-50">
              Error loading patients: {(error as Error).message}
            </div>
          ) : patients.length === 0 ? (
            <div className="text-center py-20 text-gray-500">
              <div className="bg-gray-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <User className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-lg font-medium text-gray-900">No patients found</p>
              <p className="text-sm mt-1">Try adjusting your search or add a new patient.</p>
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-gray-50/50">
                <TableRow className="hover:bg-transparent">
                  <TableHead className="font-semibold text-gray-600">Patient</TableHead>
                  <TableHead className="font-semibold text-gray-600">Contact Info</TableHead>
                  <TableHead className="font-semibold text-gray-600">MRN</TableHead>
                  <TableHead className="font-semibold text-gray-600">Date of Birth</TableHead>
                  <TableHead className="font-semibold text-gray-600">Status</TableHead>
                  <TableHead className="text-right font-semibold text-gray-600">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {patients.map((patient) => (
                  <TableRow key={patient.id} className="hover:bg-blue-50/30 transition-colors group">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9 border border-gray-100">
                          <AvatarImage src={patient.avatar_url} />
                          <AvatarFallback className="bg-blue-50 text-blue-600 text-xs font-bold">
                            {patient.name
                              .split(' ')
                              .map((n) => n[0])
                              .join('')
                              .toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium text-gray-900">{patient.name}</div>
                          <div className="text-xs text-gray-500">
                            {patient.gender || 'Not specified'}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        {patient.phone && (
                          <div className="flex items-center gap-2 text-xs text-gray-600">
                            <Phone className="w-3 h-3 text-gray-400" />
                            {patient.phone}
                          </div>
                        )}
                        {patient.email && (
                          <div className="flex items-center gap-2 text-xs text-gray-600">
                            <Mail className="w-3 h-3 text-gray-400" />
                            {patient.email}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-[10px] bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded font-mono border border-gray-200">
                        {patient.mrn}
                      </code>
                    </TableCell>
                    <TableCell className="text-sm text-gray-600">
                      {patient.date_of_birth
                        ? formatDate(patient.date_of_birth, 'MMM d, yyyy')
                        : '-'}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          patient.status === 'active'
                            ? 'success'
                            : patient.status === 'inactive'
                              ? 'secondary'
                              : 'warning'
                        }
                        className={
                          patient.status === 'active'
                            ? 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100'
                            : 'bg-gray-100 text-gray-600 border-gray-200'
                        }
                      >
                        {patient.status || 'Unknown'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Link href={`/dashboard/patients/${patient.id}`}>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-blue-600 hover:bg-blue-50">
                            <Eye className="w-4 h-4" />
                          </Button>
                        </Link>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50">
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-gray-900">
                          <MoreVertical className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
