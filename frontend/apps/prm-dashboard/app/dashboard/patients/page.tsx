'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Search, Plus, User, Phone, Mail, Eye, Activity, Users, AlertCircle, TrendingUp, Calendar } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { patientsAPI } from '@/lib/api/patients';
import {
  Card,
  CardContent,
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
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Label } from '@/components/ui/label';
import { formatDate } from '@/lib/utils/date';
import { TableSkeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';

// Flat Stat Card Component
function FlatStatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color
}: {
  title: string;
  value: number | string;
  subtitle: string;
  icon: any;
  color: 'blue' | 'green' | 'indigo' | 'amber'
}) {
  const colors = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    green: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800',
    indigo: 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-200 dark:border-indigo-800',
    amber: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
  };
  const iconColors = {
    blue: 'text-blue-500',
    green: 'text-emerald-500',
    indigo: 'text-indigo-500',
    amber: 'text-amber-500',
  };
  const valueColors = {
    blue: 'text-blue-600 dark:text-blue-400',
    green: 'text-emerald-600 dark:text-emerald-400',
    indigo: 'text-indigo-600 dark:text-indigo-400',
    amber: 'text-amber-600 dark:text-amber-400',
  };

  return (
    <div className={`${colors[color]} border-2 rounded-lg p-5 transition-all duration-200 hover:scale-[1.02]`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</span>
        <Icon className={`w-5 h-5 ${iconColors[color]}`} />
      </div>
      <div className={`text-3xl font-bold ${valueColors[color]}`}>{value}</div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
    </div>
  );
}

export default function PatientsPage() {
  const { toast } = useToast();
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

  // Fetch patient statistics
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
      toast({ title: 'Success', description: 'Patient created successfully' });
    },
    onError: (error: any) => {
      toast({ title: 'Error', description: 'Failed to create patient: ' + error.message, variant: 'destructive' });
    },
  });

  // Search patients
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast({ title: 'Validation Error', description: 'Please enter a search term', variant: 'destructive' });
      return;
    }
    const [results, error] = await patientsAPI.search(searchQuery, searchType);
    if (error) {
      toast({ title: 'Search Failed', description: error.message, variant: 'destructive' });
      return;
    }
    toast({ title: 'Search Complete', description: `Found ${results?.length || 0} patients` });
  };

  // Handle add form submit
  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!addForm.first_name || !addForm.last_name || !addForm.date_of_birth) {
      toast({ title: 'Missing Fields', description: 'Please fill in required fields', variant: 'destructive' });
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
    <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Flat Header */}
      <header className="sticky top-0 z-30 flex items-center justify-between p-6 bg-white dark:bg-gray-900 border-b-2 border-gray-100 dark:border-gray-800">
        <div>
          <h1 className="text-2xl font-heading text-gray-900 dark:text-white">Patients</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage your patient directory and records</p>
        </div>
        <Button
          onClick={() => setIsAddOpen(true)}
          className="flat-btn-primary"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Patient
        </Button>
      </header>

      <div className="p-6 space-y-6">
        {/* Flat Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <FlatStatCard
            title="Total Patients"
            value={totalCount}
            subtitle={maleCount > 0 || femaleCount > 0 ? `${maleCount} male, ${femaleCount} female` : 'All registered patients'}
            icon={Users}
            color="blue"
          />
          <FlatStatCard
            title="Active"
            value={activeCount}
            subtitle={`${totalCount > 0 ? Math.round((activeCount / totalCount) * 100) : 0}% of total`}
            icon={Activity}
            color="green"
          />
          <FlatStatCard
            title="New This Month"
            value={newThisMonth}
            subtitle="Recent registrations"
            icon={TrendingUp}
            color="indigo"
          />
          <FlatStatCard
            title="Avg Age"
            value={stats?.average_age ? Math.round(stats.average_age) : '--'}
            subtitle="Years old"
            icon={User}
            color="amber"
          />
        </div>

        {/* Flat Search Bar */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border-2 border-gray-100 dark:border-gray-700 flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search by name, MRN, or phone..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="pl-10 border-2 border-gray-200 dark:border-gray-600 focus:border-blue-500 rounded-lg bg-gray-50 dark:bg-gray-700"
            />
          </div>
          <div className="flex items-center gap-3">
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value as any)}
              className="h-10 px-4 py-2 border-2 border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-200 focus:outline-none focus:border-blue-500 bg-gray-50 dark:bg-gray-700"
            >
              <option value="name">Name</option>
              <option value="phone">Phone</option>
              <option value="mrn">MRN</option>
            </select>
            <Button onClick={handleSearch} variant="outline" className="h-10 border-2 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700">
              Search
            </Button>
          </div>
        </div>

        {/* Flat Patients Table */}
        <Card className="border-2 border-gray-100 dark:border-gray-700 rounded-lg overflow-hidden">
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-4">
                <TableSkeleton rows={5} />
              </div>
            ) : error ? (
              <div className="p-6">
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error Loading Patients</AlertTitle>
                  <AlertDescription>{(error as Error).message}</AlertDescription>
                </Alert>
              </div>
            ) : patients.length === 0 ? (
              <div className="text-center py-20 text-gray-500">
                <div className="bg-gray-100 dark:bg-gray-800 w-16 h-16 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <User className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-lg font-medium text-gray-700 dark:text-gray-300">No patients found</p>
                <p className="text-sm mt-1">Try adjusting your search or add a new patient.</p>
              </div>
            ) : (
              <Table>
                <TableHeader className="bg-gray-50 dark:bg-gray-800">
                  <TableRow className="hover:bg-transparent border-b-2 border-gray-100 dark:border-gray-700">
                    <TableHead className="font-semibold text-gray-600 dark:text-gray-300">Patient</TableHead>
                    <TableHead className="font-semibold text-gray-600 dark:text-gray-300">Contact Info</TableHead>
                    <TableHead className="font-semibold text-gray-600 dark:text-gray-300">MRN</TableHead>
                    <TableHead className="font-semibold text-gray-600 dark:text-gray-300">Date of Birth</TableHead>
                    <TableHead className="font-semibold text-gray-600 dark:text-gray-300">Status</TableHead>
                    <TableHead className="text-right font-semibold text-gray-600 dark:text-gray-300">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {patients.map((patient) => (
                    <TableRow key={patient.id} className="hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-colors border-b border-gray-100 dark:border-gray-800">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-9 w-9 rounded-lg border-2 border-gray-200 dark:border-gray-600">
                            <AvatarImage src={patient.avatar_url} />
                            <AvatarFallback className="bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-bold rounded-lg">
                              {(patient.name || patient.legal_name || `${patient.first_name || ''} ${patient.last_name || ''}`.trim() || 'P')
                                .split(' ')
                                .map((n: any) => n[0])
                                .join('')
                                .toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium text-gray-900 dark:text-white">{patient.name || patient.legal_name || `${patient.first_name || ''} ${patient.last_name || ''}`.trim() || 'Unknown'}</div>
                            <div className="text-xs text-gray-500">{patient.gender || 'Not specified'}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {patient.phone_primary && (
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <Phone className="w-3 h-3" />
                              {patient.phone_primary}
                            </div>
                          )}
                          {patient.email_primary && (
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <Mail className="w-3 h-3" />
                              {patient.email_primary}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-[10px] bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-2 py-1 rounded-md font-mono border-2 border-gray-200 dark:border-gray-700">
                          {patient.mrn}
                        </code>
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {patient.date_of_birth ? formatDate(patient.date_of_birth, 'MMM d, yyyy') : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            patient.status === 'active'
                              ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-2 border-emerald-200 dark:border-emerald-800'
                              : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-2 border-gray-200 dark:border-gray-700'
                          }
                        >
                          {patient.status || 'Unknown'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/dashboard/patients/${patient.id}`}>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-all duration-200 hover:scale-105">
                            <Eye className="w-4 h-4" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Flat Add Patient Dialog */}
      <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
        <DialogContent className="sm:max-w-[520px] p-0 overflow-hidden rounded-lg border-2 border-gray-200 dark:border-gray-700">
          {/* Flat Header */}
          <div className="bg-blue-500 px-6 py-5 text-white">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white rounded-lg">
                <Plus className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <DialogTitle className="text-lg font-heading text-white">Add New Patient</DialogTitle>
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
                  <Label htmlFor="add_first_name" className="text-sm font-medium flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-gray-400" />
                    First Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="add_first_name"
                    value={addForm.first_name}
                    onChange={(e) => setAddForm({ ...addForm, first_name: e.target.value })}
                    className="h-11 rounded-lg border-2 border-gray-200 dark:border-gray-600 focus:border-blue-500"
                    placeholder="John"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="add_last_name" className="text-sm font-medium flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-gray-400" />
                    Last Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="add_last_name"
                    value={addForm.last_name}
                    onChange={(e) => setAddForm({ ...addForm, last_name: e.target.value })}
                    className="h-11 rounded-lg border-2 border-gray-200 dark:border-gray-600 focus:border-blue-500"
                    placeholder="Doe"
                    required
                  />
                </div>
              </div>

              {/* DOB and Gender Row */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="add_dob" className="text-sm font-medium flex items-center gap-2">
                    <Calendar className="h-3.5 w-3.5 text-gray-400" />
                    Date of Birth <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="add_dob"
                    type="date"
                    value={addForm.date_of_birth}
                    onChange={(e) => setAddForm({ ...addForm, date_of_birth: e.target.value })}
                    className="h-11 rounded-lg border-2 border-gray-200 dark:border-gray-600 focus:border-blue-500"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="add_gender" className="text-sm font-medium flex items-center gap-2">
                    <Users className="h-3.5 w-3.5 text-gray-400" />
                    Gender
                  </Label>
                  <select
                    id="add_gender"
                    value={addForm.gender}
                    onChange={(e) => setAddForm({ ...addForm, gender: e.target.value })}
                    className="h-11 w-full rounded-lg border-2 border-gray-200 dark:border-gray-600 px-3 text-sm focus:border-blue-500 bg-white dark:bg-gray-800 outline-none"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              {/* Phone */}
              <div className="space-y-2">
                <Label htmlFor="add_phone" className="text-sm font-medium flex items-center gap-2">
                  <Phone className="h-3.5 w-3.5 text-gray-400" />
                  Phone Number
                </Label>
                <Input
                  id="add_phone"
                  value={addForm.phone_primary}
                  onChange={(e) => setAddForm({ ...addForm, phone_primary: e.target.value })}
                  className="h-11 rounded-lg border-2 border-gray-200 dark:border-gray-600 focus:border-blue-500"
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="add_email" className="text-sm font-medium flex items-center gap-2">
                  <Mail className="h-3.5 w-3.5 text-gray-400" />
                  Email Address
                </Label>
                <Input
                  id="add_email"
                  type="email"
                  value={addForm.email_primary}
                  onChange={(e) => setAddForm({ ...addForm, email_primary: e.target.value })}
                  className="h-11 rounded-lg border-2 border-gray-200 dark:border-gray-600 focus:border-blue-500"
                  placeholder="john.doe@email.com"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 mt-6 pt-5 border-t-2 border-gray-100 dark:border-gray-700">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsAddOpen(false)}
                className="px-5 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending}
                className="flat-btn-primary px-6"
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
