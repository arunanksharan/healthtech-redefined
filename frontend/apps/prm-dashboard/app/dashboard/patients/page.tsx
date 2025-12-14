'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Search, Plus, User, Phone, Mail, Eye, Edit, MoreVertical, Activity, Users, Clock, AlertCircle, TrendingUp, Calendar } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { patientsAPI, PatientStatistics } from '@/lib/api/patients';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { MagicCard } from '@/components/ui/magic-card';
import { Label } from '@/components/ui/label';
import { formatDate } from '@/lib/utils/date';
import toast from 'react-hot-toast';

export default function PatientsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<'name' | 'phone' | 'mrn'>('name');
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [addForm, setAddForm] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'male',
    phone_primary: '',
    email_primary: '',
  });
  const queryClient = useQueryClient();

  // Fetch all patients
  const { data: patientsData, isLoading, error } = useQuery({
    queryKey: ['patients'],
    queryFn: async () => {
      const [data, error] = await patientsAPI.getAll();
      if (error) throw new Error(error.message);
      return data;
    },
  });

  // Fetch patient statistics from API
  const { data: stats } = useQuery({
    queryKey: ['patient-stats'],
    queryFn: async () => {
      const [data, error] = await patientsAPI.getStats();
      if (error) throw new Error(error.message);
      return data;
    },
  });

  // Create patient mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof addForm) => patientsAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      queryClient.invalidateQueries({ queryKey: ['patient-stats'] });
      setIsAddOpen(false);
      setAddForm({
        first_name: '',
        last_name: '',
        date_of_birth: '',
        gender: 'male',
        phone_primary: '',
        email_primary: '',
      });
      toast.success('Patient created successfully');
    },
    onError: (error: any) => {
      toast.error('Failed to create patient: ' + error.message);
    },
  });

  // Delete patient mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => patientsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      queryClient.invalidateQueries({ queryKey: ['patient-stats'] });
      toast.success('Patient deactivated successfully');
    },
    onError: (error: any) => {
      toast.error('Failed to deactivate patient: ' + error.message);
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

  // Handle add form submit
  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!addForm.first_name || !addForm.last_name || !addForm.date_of_birth) {
      toast.error('Please fill in required fields');
      return;
    }
    createMutation.mutate(addForm);
  };

  const patients = patientsData?.items || [];
  const totalCount = stats?.total_patients ?? patientsData?.total ?? 0;
  const activeCount = stats?.active_patients ?? patients.filter((p) => p.status === 'active').length;
  const newThisMonth = stats?.new_this_month ?? 0;
  const maleCount = stats?.by_gender?.male ?? 0;
  const femaleCount = stats?.by_gender?.female ?? 0;

  return (
    <div className="flex flex-col min-h-screen bg-muted/40">
      {/* Sticky Glassmorphic Header */}
      <header className="sticky top-0 z-30 flex items-center justify-between p-6 bg-background/80 backdrop-blur-md border-b border-border/50 supports-[backdrop-filter]:bg-background/60">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Patients</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your patient directory and records</p>
        </div>
        <Button
          onClick={() => setIsAddOpen(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-all hover:scale-105"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Patient
        </Button>
      </header>

      <div className="p-6 space-y-6">
        {/* Magic Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#eff6ff">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-gray-500">Total Patients</CardTitle>
              <Users className="w-4 h-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{totalCount}</div>
              <p className="text-xs text-gray-500 mt-1">
                {maleCount > 0 || femaleCount > 0
                  ? `${maleCount} male, ${femaleCount} female`
                  : 'All registered patients'}
              </p>
            </CardContent>
          </MagicCard>

          <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#f0fdf4">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-gray-500">Active</CardTitle>
              <Activity className="w-4 h-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{activeCount}</div>
              <p className="text-xs text-green-600 mt-1 font-medium">
                {totalCount > 0 ? Math.round((activeCount / totalCount) * 100) : 0}% of total
              </p>
            </CardContent>
          </MagicCard>

          <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#eff6ff">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-gray-500">New This Month</CardTitle>
              <TrendingUp className="w-4 h-4 text-indigo-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{newThisMonth}</div>
              <p className="text-xs text-gray-500 mt-1">Recent registrations</p>
            </CardContent>
          </MagicCard>

          <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#fefce8">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-gray-500">Avg Age</CardTitle>
              <User className="w-4 h-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {stats?.average_age ? Math.round(stats.average_age) : '--'}
              </div>
              <p className="text-xs text-amber-600 mt-1 font-medium">Years old</p>
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
                              {(patient.name || patient.legal_name || 'P')
                                .split(' ')
                                .map((n) => n[0])
                                .join('')
                                .toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium text-gray-900">{patient.name || patient.legal_name || 'Unknown'}</div>
                            <div className="text-xs text-gray-500">
                              {patient.gender || 'Not specified'}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {(patient.phone || patient.primary_phone) && (
                            <div className="flex items-center gap-2 text-xs text-gray-600">
                              <Phone className="w-3 h-3 text-gray-400" />
                              {patient.phone || patient.primary_phone}
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

      {/* Add Patient Dialog */}
      <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
        <DialogContent className="sm:max-w-[520px] p-0 overflow-hidden rounded-2xl border-gray-200">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5 text-white">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-xl">
                <Plus className="h-5 w-5" />
              </div>
              <div>
                <DialogTitle className="text-lg font-semibold text-white">Add New Patient</DialogTitle>
                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                  Enter patient information to create a new record
                </DialogDescription>
              </div>
            </div>
          </div>

          <form onSubmit={handleAddSubmit} className="px-6 py-5">
            <div className="space-y-5">
              {/* Name Row */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="add_first_name" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-gray-400" />
                    First Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="add_first_name"
                    value={addForm.first_name}
                    onChange={(e) => setAddForm({ ...addForm, first_name: e.target.value })}
                    className="h-11 rounded-xl border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
                    placeholder="John"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="add_last_name" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-gray-400" />
                    Last Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="add_last_name"
                    value={addForm.last_name}
                    onChange={(e) => setAddForm({ ...addForm, last_name: e.target.value })}
                    className="h-11 rounded-xl border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
                    placeholder="Doe"
                    required
                  />
                </div>
              </div>

              {/* DOB and Gender Row */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="add_dob" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <Calendar className="h-3.5 w-3.5 text-gray-400" />
                    Date of Birth <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="add_dob"
                    type="date"
                    value={addForm.date_of_birth}
                    onChange={(e) => setAddForm({ ...addForm, date_of_birth: e.target.value })}
                    className="h-11 rounded-xl border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="add_gender" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <Users className="h-3.5 w-3.5 text-gray-400" />
                    Gender
                  </Label>
                  <select
                    id="add_gender"
                    value={addForm.gender}
                    onChange={(e) => setAddForm({ ...addForm, gender: e.target.value })}
                    className="h-11 w-full rounded-xl border border-gray-200 px-3 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 bg-gray-50/50 outline-none"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              {/* Phone */}
              <div className="space-y-2">
                <Label htmlFor="add_phone" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Phone className="h-3.5 w-3.5 text-gray-400" />
                  Phone Number
                </Label>
                <Input
                  id="add_phone"
                  value={addForm.phone_primary}
                  onChange={(e) => setAddForm({ ...addForm, phone_primary: e.target.value })}
                  className="h-11 rounded-xl border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="add_email" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Mail className="h-3.5 w-3.5 text-gray-400" />
                  Email Address
                </Label>
                <Input
                  id="add_email"
                  type="email"
                  value={addForm.email_primary}
                  onChange={(e) => setAddForm({ ...addForm, email_primary: e.target.value })}
                  className="h-11 rounded-xl border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
                  placeholder="john.doe@email.com"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 mt-6 pt-5 border-t border-gray-100">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsAddOpen(false)}
                className="rounded-full px-5 border-gray-200 hover:bg-gray-50"
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
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Patient
                  </>
                )}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
