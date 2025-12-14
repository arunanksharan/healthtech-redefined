'use client';

import { useState } from 'react';
import { Search, Plus, User, Phone, Mail, Edit, MoreVertical, Stethoscope, Users, Activity, TrendingUp, GraduationCap, CheckCircle, XCircle, BadgeCheck } from 'lucide-react';
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
                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--info) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Total Practitioners</CardTitle>
                            <Users className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">{totalCount}</div>
                            <p className="text-xs text-muted-foreground mt-1">Healthcare providers</p>
                        </CardContent>
                    </MagicCard>

                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--success) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Active</CardTitle>
                            <Activity className="w-4 h-4 text-green-600 dark:text-green-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">{activeCount}</div>
                            <p className="text-xs text-green-600 dark:text-green-400 mt-1 font-medium">
                                {totalCount > 0 ? Math.round((activeCount / totalCount) * 100) : 0}% of total
                            </p>
                        </CardContent>
                    </MagicCard>

                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--destructive) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Inactive</CardTitle>
                            <TrendingUp className="w-4 h-4 text-red-500 dark:text-red-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">{inactiveCount}</div>
                            <p className="text-xs text-muted-foreground mt-1">Not currently active</p>
                        </CardContent>
                    </MagicCard>

                    <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--channel-voice) / 0.15)">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Specialities</CardTitle>
                            <Stethoscope className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-foreground">{uniqueSpecialities}</div>
                            <p className="text-xs text-purple-600 dark:text-purple-400 mt-1 font-medium">Different specialties</p>
                        </CardContent>
                    </MagicCard>
                </div>

                {/* Search & Filters Bar */}
                <div className="bg-card p-4 rounded-xl border border-border shadow-sm flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                            placeholder="Search by name or speciality..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                            className="pl-10 border-border focus:border-blue-300 dark:focus:border-blue-600 focus:ring-blue-100 dark:focus:ring-blue-900/30 bg-muted/50"
                        />
                    </div>
                    <div className="flex items-center gap-3">
                        <select
                            value={specialityFilter}
                            onChange={(e) => setSpecialityFilter(e.target.value)}
                            className="h-10 px-4 py-2 border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-900/30 bg-muted/50"
                        >
                            <option value="all">All Specialities</option>
                            {specialities?.map((spec) => (
                                <option key={spec} value={spec}>
                                    {spec}
                                </option>
                            ))}
                        </select>
                        <Button onClick={handleSearch} variant="outline" className="h-10 border-border hover:bg-accent text-muted-foreground">
                            Search
                        </Button>
                    </div>
                </div>

                {/* Practitioners Table */}
                <Card className="border-border shadow-sm overflow-hidden">
                    <CardContent className="p-0">
                        {isLoading ? (
                            <div className="flex flex-col items-center justify-center py-20">
                                <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
                                <p className="text-muted-foreground text-sm">Loading practitioners...</p>
                            </div>
                        ) : error ? (
                            <div className="text-center py-12 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20">
                                Error loading practitioners: {(error as Error).message}
                            </div>
                        ) : practitioners.length === 0 ? (
                            <div className="text-center py-20 text-muted-foreground">
                                <div className="bg-muted w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Stethoscope className="w-8 h-8 text-muted-foreground/50" />
                                </div>
                                <p className="text-lg font-medium text-foreground">No practitioners found</p>
                                <p className="text-sm mt-1">Try adjusting your search or add a new practitioner.</p>
                            </div>
                        ) : (
                            <Table>
                                <TableHeader className="bg-muted/50">
                                    <TableRow className="hover:bg-transparent">
                                        <TableHead className="font-semibold text-muted-foreground">Practitioner</TableHead>
                                        <TableHead className="font-semibold text-muted-foreground">Speciality</TableHead>
                                        <TableHead className="font-semibold text-muted-foreground">License</TableHead>
                                        <TableHead className="font-semibold text-muted-foreground">Contact</TableHead>
                                        <TableHead className="font-semibold text-muted-foreground">Status</TableHead>
                                        <TableHead className="text-right font-semibold text-muted-foreground">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {practitioners.map((practitioner) => (
                                        <TableRow key={practitioner.id} className="hover:bg-blue-50/30 dark:hover:bg-blue-900/10 transition-colors group">
                                            <TableCell>
                                                <div className="flex items-center gap-3">
                                                    <Avatar className="h-9 w-9 border border-border">
                                                        <AvatarFallback className="bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-bold">
                                                            {practitioner.first_name?.[0]}
                                                            {practitioner.last_name?.[0]}
                                                        </AvatarFallback>
                                                    </Avatar>
                                                    <div>
                                                        <div className="font-medium text-foreground">
                                                            Dr. {practitioner.first_name} {practitioner.last_name}
                                                        </div>
                                                        <div className="text-xs text-muted-foreground">
                                                            {practitioner.qualification || 'No qualification'}
                                                        </div>
                                                    </div>
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline" className="bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800 font-medium">
                                                    {practitioner.speciality || 'General'}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <span className="text-sm text-muted-foreground">
                                                    {practitioner.license_number || '—'}
                                                </span>
                                            </TableCell>
                                            <TableCell>
                                                <div className="space-y-1">
                                                    {practitioner.phone_primary && (
                                                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                                                            <Phone className="w-3.5 h-3.5 text-muted-foreground/60" />
                                                            {practitioner.phone_primary}
                                                        </div>
                                                    )}
                                                    {practitioner.email_primary && (
                                                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                                                            <Mail className="w-3.5 h-3.5 text-muted-foreground/60" />
                                                            {practitioner.email_primary}
                                                        </div>
                                                    )}
                                                    {!practitioner.phone_primary && !practitioner.email_primary && (
                                                        <span className="text-muted-foreground/50">—</span>
                                                    )}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant="outline"
                                                    className={
                                                        practitioner.is_active
                                                            ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800'
                                                            : 'bg-muted text-muted-foreground border-border'
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
                <DialogContent className="sm:max-w-[520px] p-0 overflow-hidden rounded-2xl border-gray-200">
                    {/* Header with gradient */}
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5 text-white">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-white/20 rounded-xl">
                                <Plus className="h-5 w-5" />
                            </div>
                            <div>
                                <DialogTitle className="text-lg font-semibold text-white">Add New Practitioner</DialogTitle>
                                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                                    Add a new healthcare provider to your organization
                                </DialogDescription>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleAddSubmit} className="px-6 py-5">
                        <div className="space-y-5">
                            {/* Name Row */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="first_name" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <User className="h-3.5 w-3.5 text-muted-foreground" />
                                        First Name <span className="text-red-500">*</span>
                                    </Label>
                                    <Input
                                        id="first_name"
                                        value={addForm.first_name}
                                        onChange={(e) => setAddForm({ ...addForm, first_name: e.target.value })}
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        placeholder="John"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="last_name" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <User className="h-3.5 w-3.5 text-muted-foreground" />
                                        Last Name <span className="text-red-500">*</span>
                                    </Label>
                                    <Input
                                        id="last_name"
                                        value={addForm.last_name}
                                        onChange={(e) => setAddForm({ ...addForm, last_name: e.target.value })}
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        placeholder="Smith"
                                        required
                                    />
                                </div>
                            </div>

                            {/* Speciality and Qualification Row */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="speciality" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <Stethoscope className="h-3.5 w-3.5 text-muted-foreground" />
                                        Speciality
                                    </Label>
                                    <Input
                                        id="speciality"
                                        value={addForm.speciality}
                                        onChange={(e) => setAddForm({ ...addForm, speciality: e.target.value })}
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        placeholder="Cardiology"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="qualification" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <GraduationCap className="h-3.5 w-3.5 text-muted-foreground" />
                                        Qualification
                                    </Label>
                                    <Input
                                        id="qualification"
                                        value={addForm.qualification}
                                        onChange={(e) => setAddForm({ ...addForm, qualification: e.target.value })}
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        placeholder="MD, FACC"
                                    />
                                </div>
                            </div>

                            {/* Phone and Email Row */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="phone" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                                        Phone
                                    </Label>
                                    <Input
                                        id="phone"
                                        value={addForm.phone_primary}
                                        onChange={(e) => setAddForm({ ...addForm, phone_primary: e.target.value })}
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        placeholder="+1 234 567 8900"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="email" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                                        Email
                                    </Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        value={addForm.email_primary}
                                        onChange={(e) => setAddForm({ ...addForm, email_primary: e.target.value })}
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        placeholder="john.smith@hospital.com"
                                    />
                                </div>
                            </div>

                            {/* License Number */}
                            <div className="space-y-2">
                                <Label htmlFor="license" className="text-sm font-medium text-foreground flex items-center gap-2">
                                    <BadgeCheck className="h-3.5 w-3.5 text-muted-foreground" />
                                    License Number
                                </Label>
                                <Input
                                    id="license"
                                    value={addForm.license_number}
                                    onChange={(e) => setAddForm({ ...addForm, license_number: e.target.value })}
                                    className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                    placeholder="MED-12345"
                                />
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-end gap-3 mt-6 pt-5 border-t border-border">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => setIsAddOpen(false)}
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
                                        Creating...
                                    </>
                                ) : (
                                    <>
                                        <Plus className="w-4 h-4 mr-2" />
                                        Create Practitioner
                                    </>
                                )}
                            </Button>
                        </div>
                    </form>
                </DialogContent>
            </Dialog>

            {/* Edit Practitioner Dialog */}
            <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
                <DialogContent className="sm:max-w-[520px] p-0 overflow-hidden rounded-2xl border-gray-200">
                    {/* Header with gradient */}
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5 text-white">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-white/20 rounded-xl">
                                <Edit className="h-5 w-5" />
                            </div>
                            <div>
                                <DialogTitle className="text-lg font-semibold text-white">Edit Practitioner</DialogTitle>
                                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                                    Update practitioner information
                                </DialogDescription>
                            </div>
                        </div>
                    </div>

                    {selectedPractitioner && (
                        <form onSubmit={handleEditSubmit} className="px-6 py-5">
                            <div className="space-y-5">
                                {/* Name Row */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_first_name" className="text-sm font-medium text-foreground flex items-center gap-2">
                                            <User className="h-3.5 w-3.5 text-muted-foreground" />
                                            First Name <span className="text-red-500">*</span>
                                        </Label>
                                        <Input
                                            id="edit_first_name"
                                            value={selectedPractitioner.first_name}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    first_name: e.target.value,
                                                })
                                            }
                                            className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_last_name" className="text-sm font-medium text-foreground flex items-center gap-2">
                                            <User className="h-3.5 w-3.5 text-muted-foreground" />
                                            Last Name <span className="text-red-500">*</span>
                                        </Label>
                                        <Input
                                            id="edit_last_name"
                                            value={selectedPractitioner.last_name}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    last_name: e.target.value,
                                                })
                                            }
                                            className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                            required
                                        />
                                    </div>
                                </div>

                                {/* Speciality and Qualification Row */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_speciality" className="text-sm font-medium text-foreground flex items-center gap-2">
                                            <Stethoscope className="h-3.5 w-3.5 text-muted-foreground" />
                                            Speciality
                                        </Label>
                                        <Input
                                            id="edit_speciality"
                                            value={selectedPractitioner.speciality || ''}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    speciality: e.target.value,
                                                })
                                            }
                                            className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_qualification" className="text-sm font-medium text-foreground flex items-center gap-2">
                                            <GraduationCap className="h-3.5 w-3.5 text-muted-foreground" />
                                            Qualification
                                        </Label>
                                        <Input
                                            id="edit_qualification"
                                            value={selectedPractitioner.qualification || ''}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    qualification: e.target.value,
                                                })
                                            }
                                            className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        />
                                    </div>
                                </div>

                                {/* Phone and Email Row */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_phone" className="text-sm font-medium text-foreground flex items-center gap-2">
                                            <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                                            Phone
                                        </Label>
                                        <Input
                                            id="edit_phone"
                                            value={selectedPractitioner.phone_primary || ''}
                                            onChange={(e) =>
                                                setSelectedPractitioner({
                                                    ...selectedPractitioner,
                                                    phone_primary: e.target.value,
                                                })
                                            }
                                            className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="edit_email" className="text-sm font-medium text-foreground flex items-center gap-2">
                                            <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                                            Email
                                        </Label>
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
                                            className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        />
                                    </div>
                                </div>

                                {/* License Number */}
                                <div className="space-y-2">
                                    <Label htmlFor="edit_license" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <BadgeCheck className="h-3.5 w-3.5 text-muted-foreground" />
                                        License Number
                                    </Label>
                                    <Input
                                        id="edit_license"
                                        value={selectedPractitioner.license_number || ''}
                                        onChange={(e) =>
                                            setSelectedPractitioner({
                                                ...selectedPractitioner,
                                                license_number: e.target.value,
                                            })
                                        }
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                    />
                                </div>
                            </div>

                            {/* Footer */}
                            <div className="flex items-center justify-end gap-3 mt-6 pt-5 border-t border-border">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => setIsEditOpen(false)}
                                    className="rounded-full px-5 border-border hover:bg-muted"
                                >
                                    Cancel
                                </Button>
                                <Button
                                    type="submit"
                                    disabled={updateMutation.isPending}
                                    className="rounded-full px-6 bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all"
                                >
                                    {updateMutation.isPending ? (
                                        <>
                                            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <CheckCircle className="w-4 h-4 mr-2" />
                                            Save Changes
                                        </>
                                    )}
                                </Button>
                            </div>
                        </form>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
