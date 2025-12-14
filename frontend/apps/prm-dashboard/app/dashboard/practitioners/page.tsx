'use client';

import { useState } from 'react';
import { Search, Plus, User, Phone, Mail, Edit, MoreVertical, Stethoscope, Users, Activity, TrendingUp, GraduationCap, CheckCircle, XCircle } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { practitionersAPI, Practitioner, PractitionerCreate } from '@/lib/api/practitioners';
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
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from '@/components/ui/dialog';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { MagicCard } from '@/components/ui/magic-card';
import { Label } from '@/components/ui/label';
import toast from 'react-hot-toast';

// Default tenant ID for demo
const DEFAULT_TENANT_ID = '00000000-0000-0000-0000-000000000001';

export default function PractitionersPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [specialityFilter, setSpecialityFilter] = useState<string>('all');
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [isEditOpen, setIsEditOpen] = useState(false);
    const [selectedPractitioner, setSelectedPractitioner] = useState<Practitioner | null>(null);
    const [addForm, setAddForm] = useState<PractitionerCreate>({
        tenant_id: DEFAULT_TENANT_ID,
        first_name: '',
        last_name: '',
        speciality: '',
        qualification: '',
        phone_primary: '',
        email_primary: '',
        license_number: '',
        is_active: true,
    });
    const queryClient = useQueryClient();

    // Fetch all practitioners
    const { data: practitionersData, isLoading, error } = useQuery({
        queryKey: ['practitioners', searchQuery, specialityFilter],
        queryFn: async () => {
            const params: any = { page_size: 50 };
            if (searchQuery) params.search = searchQuery;
            if (specialityFilter && specialityFilter !== 'all') params.speciality = specialityFilter;
            const [data, error] = await practitionersAPI.getAll(params);
            if (error) throw new Error(error.message);
            return data;
        },
    });

    // Fetch specialities for filter
    const { data: specialities } = useQuery({
        queryKey: ['practitioner-specialities'],
        queryFn: async () => {
            const [data, error] = await practitionersAPI.getSpecialities();
            if (error) throw new Error(error.message);
            return data;
        },
    });

    // Create practitioner mutation
    const createMutation = useMutation({
        mutationFn: (data: PractitionerCreate) => practitionersAPI.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['practitioners'] });
            queryClient.invalidateQueries({ queryKey: ['practitioner-specialities'] });
            setIsAddOpen(false);
            resetAddForm();
            toast.success('Practitioner created successfully');
        },
        onError: (error: any) => {
            toast.error('Failed to create practitioner: ' + error.message);
        },
    });

    // Update practitioner mutation
    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<Practitioner> }) =>
            practitionersAPI.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['practitioners'] });
            setIsEditOpen(false);
            setSelectedPractitioner(null);
            toast.success('Practitioner updated successfully');
        },
        onError: (error: any) => {
            toast.error('Failed to update practitioner: ' + error.message);
        },
    });

    const resetAddForm = () => {
        setAddForm({
            tenant_id: DEFAULT_TENANT_ID,
            first_name: '',
            last_name: '',
            speciality: '',
            qualification: '',
            phone_primary: '',
            email_primary: '',
            license_number: '',
            is_active: true,
        });
    };

    const handleAddSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!addForm.first_name || !addForm.last_name) {
            toast.error('Please fill in required fields');
            return;
        }
        createMutation.mutate(addForm);
    };

    const handleEditSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedPractitioner) return;
        updateMutation.mutate({
            id: selectedPractitioner.id,
            data: selectedPractitioner,
        });
    };

    const handleToggleActive = (practitioner: Practitioner) => {
        updateMutation.mutate({
            id: practitioner.id,
            data: { is_active: !practitioner.is_active },
        });
    };

    const handleSearch = () => {
        // Query will refetch automatically due to queryKey dep
    };

    const practitioners = practitionersData?.items || [];
    const totalCount = practitionersData?.total || 0;
    const activeCount = practitioners.filter((p) => p.is_active).length;
    const inactiveCount = practitioners.filter((p) => !p.is_active).length;
    const uniqueSpecialities = new Set(practitioners.map((p) => p.speciality).filter(Boolean)).size;

    return (
        <div className="flex flex-col min-h-screen bg-muted/40">
            {/* Sticky Glassmorphic Header */}
            <header className="sticky top-0 z-30 flex items-center justify-between p-6 bg-background/80 backdrop-blur-md border-b border-border/50 supports-[backdrop-filter]:bg-background/60">
                <div>
                    <h1 className="text-2xl font-bold text-foreground tracking-tight">Practitioners</h1>
                    <p className="text-sm text-muted-foreground mt-1">Manage your healthcare providers and staff</p>
                </div>
                <Button
                    onClick={() => setIsAddOpen(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-all hover:scale-105"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Practitioner
                </Button>
            </header>

            <div className="p-6 space-y-6">
                {/* Magic Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#eff6ff">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-gray-500">Total Practitioners</CardTitle>
                            <Users className="w-4 h-4 text-blue-600" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-gray-900">{totalCount}</div>
                            <p className="text-xs text-gray-500 mt-1">Healthcare providers</p>
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

                    <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#fef2f2">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-gray-500">Inactive</CardTitle>
                            <TrendingUp className="w-4 h-4 text-red-500" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-gray-900">{inactiveCount}</div>
                            <p className="text-xs text-gray-500 mt-1">Not currently active</p>
                        </CardContent>
                    </MagicCard>

                    <MagicCard className="bg-white border border-gray-200 shadow-sm" gradientColor="#faf5ff">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-gray-500">Specialities</CardTitle>
                            <Stethoscope className="w-4 h-4 text-purple-600" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-gray-900">{uniqueSpecialities}</div>
                            <p className="text-xs text-purple-600 mt-1 font-medium">Different specialties</p>
                        </CardContent>
                    </MagicCard>
                </div>

                {/* Search & Filters Bar */}
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <Input
                            placeholder="Search by name or speciality..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                            className="pl-10 border-gray-200 focus:border-blue-300 focus:ring-blue-100 bg-gray-50/50"
                        />
                    </div>
                    <div className="flex items-center gap-3">
                        <select
                            value={specialityFilter}
                            onChange={(e) => setSpecialityFilter(e.target.value)}
                            className="h-10 px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-100 bg-gray-50/50"
                        >
                            <option value="all">All Specialities</option>
                            {specialities?.map((spec) => (
                                <option key={spec} value={spec}>
                                    {spec}
                                </option>
                            ))}
                        </select>
                        <Button onClick={handleSearch} variant="outline" className="h-10 border-gray-200 hover:bg-gray-50 text-gray-700">
                            Search
                        </Button>
                    </div>
                </div>

                {/* Practitioners Table */}
                <Card className="border-gray-200 shadow-sm overflow-hidden">
                    <CardContent className="p-0">
                        {isLoading ? (
                            <div className="flex flex-col items-center justify-center py-20">
                                <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
                                <p className="text-gray-500 text-sm">Loading practitioners...</p>
                            </div>
                        ) : error ? (
                            <div className="text-center py-12 text-red-600 bg-red-50">
                                Error loading practitioners: {(error as Error).message}
                            </div>
                        ) : practitioners.length === 0 ? (
                            <div className="text-center py-20 text-gray-500">
                                <div className="bg-gray-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Stethoscope className="w-8 h-8 text-gray-400" />
                                </div>
                                <p className="text-lg font-medium text-gray-900">No practitioners found</p>
                                <p className="text-sm mt-1">Try adjusting your search or add a new practitioner.</p>
                            </div>
                        ) : (
                            <Table>
                                <TableHeader className="bg-gray-50/50">
                                    <TableRow className="hover:bg-transparent">
                                        <TableHead className="font-semibold text-gray-600">Practitioner</TableHead>
                                        <TableHead className="font-semibold text-gray-600">Speciality</TableHead>
                                        <TableHead className="font-semibold text-gray-600">License</TableHead>
                                        <TableHead className="font-semibold text-gray-600">Contact</TableHead>
                                        <TableHead className="font-semibold text-gray-600">Status</TableHead>
                                        <TableHead className="text-right font-semibold text-gray-600">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {practitioners.map((practitioner) => (
                                        <TableRow key={practitioner.id} className="hover:bg-blue-50/30 transition-colors group">
                                            <TableCell>
                                                <div className="flex items-center gap-3">
                                                    <Avatar className="h-9 w-9 border border-gray-100">
                                                        <AvatarFallback className="bg-blue-50 text-blue-600 text-xs font-bold">
                                                            {practitioner.first_name?.[0]}
                                                            {practitioner.last_name?.[0]}
                                                        </AvatarFallback>
                                                    </Avatar>
                                                    <div>
                                                        <div className="font-medium text-gray-900">
                                                            Dr. {practitioner.first_name} {practitioner.last_name}
                                                        </div>
                                                        <div className="text-xs text-gray-500">
                                                            {practitioner.qualification || 'No qualification'}
                                                        </div>
                                                    </div>
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200 font-medium">
                                                    {practitioner.speciality || 'General'}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <span className="text-sm text-gray-600">
                                                    {practitioner.license_number || '—'}
                                                </span>
                                            </TableCell>
                                            <TableCell>
                                                <div className="space-y-1">
                                                    {practitioner.phone_primary && (
                                                        <div className="flex items-center gap-1.5 text-sm text-gray-600">
                                                            <Phone className="w-3.5 h-3.5 text-gray-400" />
                                                            {practitioner.phone_primary}
                                                        </div>
                                                    )}
                                                    {practitioner.email_primary && (
                                                        <div className="flex items-center gap-1.5 text-sm text-gray-600">
                                                            <Mail className="w-3.5 h-3.5 text-gray-400" />
                                                            {practitioner.email_primary}
                                                        </div>
                                                    )}
                                                    {!practitioner.phone_primary && !practitioner.email_primary && (
                                                        <span className="text-gray-400">—</span>
                                                    )}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant="outline"
                                                    className={
                                                        practitioner.is_active
                                                            ? 'bg-green-50 text-green-700 border-green-200'
                                                            : 'bg-gray-100 text-gray-600 border-gray-200'
                                                    }
                                                >
                                                    {practitioner.is_active ? 'Active' : 'Inactive'}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <MoreVertical className="h-4 w-4" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end">
                                                        <DropdownMenuItem
                                                            onClick={() => {
                                                                setSelectedPractitioner(practitioner);
                                                                setIsEditOpen(true);
                                                            }}
                                                        >
                                                            <Edit className="mr-2 h-4 w-4" />
                                                            Edit Details
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem onClick={() => handleToggleActive(practitioner)}>
                                                            {practitioner.is_active ? (
                                                                <>
                                                                    <XCircle className="mr-2 h-4 w-4 text-red-500" />
                                                                    <span className="text-red-600">Deactivate</span>
                                                                </>
                                                            ) : (
                                                                <>
                                                                    <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                                                                    <span className="text-green-600">Activate</span>
                                                                </>
                                                            )}
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Add Practitioner Dialog */}
            <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                        <DialogTitle>Add New Practitioner</DialogTitle>
                        <DialogDescription>
                            Add a new healthcare provider to your organization
                        </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleAddSubmit}>
                        <div className="grid gap-4 py-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="first_name">First Name *</Label>
                                    <Input
                                        id="first_name"
                                        value={addForm.first_name}
                                        onChange={(e) => setAddForm({ ...addForm, first_name: e.target.value })}
                                        placeholder="John"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="last_name">Last Name *</Label>
                                    <Input
                                        id="last_name"
                                        value={addForm.last_name}
                                        onChange={(e) => setAddForm({ ...addForm, last_name: e.target.value })}
                                        placeholder="Smith"
                                        required
                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="speciality">Speciality</Label>
                                    <Input
                                        id="speciality"
                                        value={addForm.speciality}
                                        onChange={(e) => setAddForm({ ...addForm, speciality: e.target.value })}
                                        placeholder="Cardiology"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="qualification">Qualification</Label>
                                    <Input
                                        id="qualification"
                                        value={addForm.qualification}
                                        onChange={(e) => setAddForm({ ...addForm, qualification: e.target.value })}
                                        placeholder="MD, FACC"
                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="phone">Phone</Label>
                                    <Input
                                        id="phone"
                                        value={addForm.phone_primary}
                                        onChange={(e) => setAddForm({ ...addForm, phone_primary: e.target.value })}
                                        placeholder="+1 234 567 8900"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="email">Email</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        value={addForm.email_primary}
                                        onChange={(e) => setAddForm({ ...addForm, email_primary: e.target.value })}
                                        placeholder="john.smith@hospital.com"
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="license">License Number</Label>
                                <Input
                                    id="license"
                                    value={addForm.license_number}
                                    onChange={(e) => setAddForm({ ...addForm, license_number: e.target.value })}
                                    placeholder="MED-12345"
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)}>
                                Cancel
                            </Button>
                            <Button type="submit" disabled={createMutation.isPending} className="bg-blue-600 hover:bg-blue-700">
                                {createMutation.isPending ? 'Creating...' : 'Create Practitioner'}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>

            {/* Edit Practitioner Dialog */}
            <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
                <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                        <DialogTitle>Edit Practitioner</DialogTitle>
                        <DialogDescription>Update practitioner information</DialogDescription>
                    </DialogHeader>
                    {selectedPractitioner && (
                        <form onSubmit={handleEditSubmit}>
                            <div className="grid gap-4 py-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_first_name">First Name *</Label>
                                        <Input
                                            id="edit_first_name"
                                            value={selectedPractitioner.first_name}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    first_name: e.target.value,
                                                })
                                            }
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_last_name">Last Name *</Label>
                                        <Input
                                            id="edit_last_name"
                                            value={selectedPractitioner.last_name}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    last_name: e.target.value,
                                                })
                                            }
                                            required
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_speciality">Speciality</Label>
                                        <Input
                                            id="edit_speciality"
                                            value={selectedPractitioner.speciality || ''}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    speciality: e.target.value,
                                                })
                                            }
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_qualification">Qualification</Label>
                                        <Input
                                            id="edit_qualification"
                                            value={selectedPractitioner.qualification || ''}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    qualification: e.target.value,
                                                })
                                            }
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_phone">Phone</Label>
                                        <Input
                                            id="edit_phone"
                                            value={selectedPractitioner.phone_primary || ''}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    phone_primary: e.target.value,
                                                })
                                            }
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_email">Email</Label>
                                        <Input
                                            id="edit_email"
                                            type="email"
                                            value={selectedPractitioner.email_primary || ''}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    email_primary: e.target.value,
                                                })
                                            }
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="edit_license">License Number</Label>
                                    <Input
                                        id="edit_license"
                                        value={selectedPractitioner.license_number || ''}
                                        onChange={(e) =>
                                            setSelectedPractitioner({
                                                ...selectedPractitioner,
                                                license_number: e.target.value,
                                            })
                                        }
                                    />
                                </div>
                            </div>
                            <DialogFooter>
                                <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)}>
                                    Cancel
                                </Button>
                                <Button type="submit" disabled={updateMutation.isPending} className="bg-blue-600 hover:bg-blue-700">
                                    {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                                </Button>
                            </DialogFooter>
                        </form>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
