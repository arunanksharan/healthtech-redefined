'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
    Plus,
    Search,
    Building2,
    MapPin,
    Globe,
    Phone,
    Activity,
    Stethoscope,
    TestTube,
    CheckCircle2,
    XCircle,
    Building,
    MoreHorizontal,
    Pencil,
    Trash2,
    AlertTriangle
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { MagicCard } from '@/components/ui/magic-card';
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
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import {
    getOrganizations,
    createOrganization,
    updateOrganization,
    deleteOrganization
} from '@/lib/api/organizations';
import { Organization } from '@/lib/api/types';

export default function OrganizationsPage() {
    const { toast } = useToast();
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [searchQuery, setSearchQuery] = useState('');

    // Dialog State
    const [open, setOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Edit/Delete State
    const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
    const [orgToDelete, setOrgToDelete] = useState<Organization | null>(null);

    const [formData, setFormData] = useState({
        name: '',
        type: 'hospital',
        phone: '',
        email: '',
        city: '',
        country: '',
    });

    const fetchOrganizations = async () => {
        setLoading(true);
        const [data, error] = await getOrganizations({ page: 1, page_size: 100 });

        if (error) {
            console.error('Failed to fetch organizations:', error);
            setError(error.message || 'Failed to load organizations');
            toast({ title: 'Error', description: 'Failed to load organizations', variant: 'destructive' });
        } else if (data) {
            setOrganizations(data.items);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchOrganizations();
    }, []);

    // Reset form when dialog closes
    useEffect(() => {
        if (!open) {
            setEditingOrg(null);
            setFormData({ name: '', type: 'hospital', phone: '', email: '', city: '', country: '' });
        }
    }, [open]);

    const handleEdit = (org: Organization) => {
        setEditingOrg(org);
        setFormData({
            name: org.name,
            type: org.type || 'hospital',
            phone: org.phone || '',
            email: org.email || '',
            city: org.city || '',
            country: org.country || '',
        });
        setOpen(true);
    };

    const handleDeleteClick = (org: Organization) => {
        setOrgToDelete(org);
        setDeleteDialogOpen(true);
    };

    const confirmDelete = async () => {
        if (!orgToDelete) return;

        setSubmitting(true);
        const [, error] = await deleteOrganization(orgToDelete.id);

        if (error) {
            toast({ title: 'Error', description: error.message || 'Failed to delete organization', variant: 'destructive' });
        } else {
            toast({ title: 'Success', description: 'Organization deleted successfully', variant: 'default' });
            fetchOrganizations();
        }
        setSubmitting(false);
        setDeleteDialogOpen(false);
        setOrgToDelete(null);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name) {
            toast({ title: 'Validation Error', description: 'Organization Name is required', variant: 'destructive' });
            return;
        }

        setSubmitting(true);

        let error;
        let result;

        if (editingOrg) {
            // Update existing
            [result, error] = await updateOrganization(editingOrg.id, formData);
        } else {
            // Create new
            [result, error] = await createOrganization({
                ...formData,
                tenant_id: '00000000-0000-0000-0000-000000000001', // TODO: Get from auth context
            });
        }

        if (error) {
            console.error(`Failed to ${editingOrg ? 'update' : 'create'} organization:`, error);
            toast({ title: 'Error', description: error.message || `Failed to ${editingOrg ? 'update' : 'create'} organization`, variant: 'destructive' });
        } else if (result) {
            toast({ title: 'Success', description: `Organization ${editingOrg ? 'updated' : 'created'} successfully`, variant: 'default' });
            setOpen(false);
            fetchOrganizations(); // Refresh list
        }
        setSubmitting(false);
    };

    const filteredOrgs = organizations.filter(org =>
        org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (org.type && org.type.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    // Calculate Stats
    const stats = {
        total: organizations.length,
        active: organizations.filter(o => o.is_active).length,
        hospitals: organizations.filter(o => o.type?.toLowerCase().includes('hospital')).length,
        clinics: organizations.filter(o => o.type?.toLowerCase().includes('clinic')).length,
        labs: organizations.filter(o => o.type?.toLowerCase().includes('lab')).length,
        inactive: organizations.filter(o => !o.is_active).length
    };

    return (
        <div className="space-y-8 pb-10">
            {/* Sticky Header */}
            <div className="flex items-center justify-between sticky top-[4rem] z-20 bg-background/90 backdrop-blur-md py-4 -mx-6 px-6 border-b border-border/50">
                <div>
                    <h1 className="text-2xl font-bold text-foreground tracking-tight">Organizations</h1>
                    <p className="text-muted-foreground text-sm">Manage healthcare facilities and partners</p>
                </div>
                <Button
                    onClick={() => setOpen(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all rounded-full px-6"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    New Organization
                </Button>
            </div>

            {/* Magic Stats */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--info) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Total</CardTitle>
                        <Building2 className="w-4 h-4 text-blue-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.total}</div>
                        <p className="text-xs text-muted-foreground mt-1">Registered Orgs</p>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--success) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Active</CardTitle>
                        <Activity className="w-4 h-4 text-green-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.active}</div>
                        <p className="text-xs text-green-600 mt-1 font-medium">Operational</p>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(217 91% 60% / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Hospitals</CardTitle>
                        <Building className="w-4 h-4 text-purple-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.hospitals}</div>
                        <p className="text-xs text-purple-600 mt-1 font-medium">Multi-specialty</p>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(142 76% 36% / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Clinics</CardTitle>
                        <Stethoscope className="w-4 h-4 text-teal-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.clinics}</div>
                        <p className="text-xs text-teal-600 mt-1 font-medium">Outpatient</p>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(47 95% 57% / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Labs</CardTitle>
                        <TestTube className="w-4 h-4 text-amber-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.labs}</div>
                        <p className="text-xs text-amber-600 mt-1 font-medium">Diagnostics</p>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--destructive) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Inactive</CardTitle>
                        <XCircle className="w-4 h-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.inactive}</div>
                        <p className="text-xs text-red-500 mt-1 font-medium">Suspended</p>
                    </CardContent>
                </MagicCard>
            </div>

            {/* Main Content Card */}
            <Card className="border-border shadow-sm">
                <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <CardTitle>Organization Directory</CardTitle>
                            <p className="text-sm text-muted-foreground">
                                A list of all registered healthcare organizations in your network.
                            </p>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="mb-6 flex flex-col sm:flex-row items-center gap-4">
                        <div className="relative flex-1 w-full">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search by name, type..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 h-10 rounded-xl bg-muted/30 border-border md:w-[350px]"
                            />
                        </div>
                    </div>

                    {error && (
                        <Alert variant="destructive" className="mb-6">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertTitle>Error</AlertTitle>
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    <div className="rounded-xl border border-border overflow-hidden">
                        <Table>
                            <TableHeader className="bg-muted/50">
                                <TableRow>
                                    <TableHead className="font-semibold">Name</TableHead>
                                    <TableHead className="font-semibold">Type</TableHead>
                                    <TableHead className="font-semibold">Contact</TableHead>
                                    <TableHead className="font-semibold">Location</TableHead>
                                    <TableHead className="font-semibold">Status</TableHead>
                                    <TableHead className="w-[80px]">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    Array.from({ length: 5 }).map((_, i) => (
                                        <TableRow key={i}>
                                            <TableCell><Skeleton className="h-4 w-[200px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[100px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[80px]" /></TableCell>
                                            <TableCell><Skeleton className="h-8 w-8 rounded-full" /></TableCell>
                                        </TableRow>
                                    ))
                                ) : filteredOrgs.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                                            No organizations found matching your search.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredOrgs.map((org) => (
                                        <TableRow key={org.id} className="group hover:bg-muted/50 transition-colors">
                                            <TableCell className="font-medium">
                                                <div className="flex items-center gap-2">
                                                    <div className="p-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                                                        <Building2 className="h-4 w-4" />
                                                    </div>
                                                    {org.name}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="secondary" className="capitalize font-medium rounded-md px-2.5 py-0.5">
                                                    {org.type}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex flex-col gap-1 text-sm text-muted-foreground">
                                                    {org.email && (
                                                        <span className="flex items-center gap-1.5">
                                                            <Globe className="h-3.5 w-3.5" /> {org.email}
                                                        </span>
                                                    )}
                                                    {org.phone && (
                                                        <span className="flex items-center gap-1.5">
                                                            <Phone className="h-3.5 w-3.5" /> {org.phone}
                                                        </span>
                                                    )}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                {org.city && (
                                                    <div className="flex items-center gap-1.5 text-muted-foreground text-sm">
                                                        <MapPin className="h-3.5 w-3.5" />
                                                        {org.city}, {org.country}
                                                    </div>
                                                )}
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    className={
                                                        org.is_active
                                                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 hover:bg-green-100'
                                                            : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 hover:bg-red-100'
                                                    }
                                                >
                                                    {org.is_active ? 'Active' : 'Inactive'}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <Button variant="ghost" className="h-8 w-8 p-0">
                                                            <span className="sr-only">Open menu</span>
                                                            <MoreHorizontal className="h-4 w-4" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end">
                                                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                                        <DropdownMenuItem onClick={() => handleEdit(org)}>
                                                            <Pencil className="mr-2 h-4 w-4" />
                                                            Edit Details
                                                        </DropdownMenuItem>
                                                        <DropdownMenuSeparator />
                                                        <DropdownMenuItem
                                                            onClick={() => handleDeleteClick(org)}
                                                            className="text-red-600 focus:text-red-600"
                                                        >
                                                            <Trash2 className="mr-2 h-4 w-4" />
                                                            Delete Organization
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>

            {/* Create/Edit Organization Dialog */}
            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent className="sm:max-w-[550px] p-0 overflow-hidden rounded-2xl border-border">
                    {/* Header with gradient */}
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5 text-white">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-white/20 rounded-xl">
                                <AlertTriangle className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <DialogTitle className="text-lg font-semibold text-white">
                                    {editingOrg ? 'Edit Organization' : 'Add New Organization'}
                                </DialogTitle>
                                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                                    {editingOrg ? 'Update organization details' : 'Register a new healthcare facility or partner'}
                                </DialogDescription>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="px-6 py-5">
                        <div className="space-y-5">
                            {/* Organization Name */}
                            <div className="space-y-2">
                                <Label htmlFor="name" className="text-sm font-medium text-foreground flex items-center gap-2">
                                    <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                                    Name <span className="text-red-500">*</span>
                                </Label>
                                <Input
                                    id="name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                    placeholder="e.g. Apollo Hospital"
                                    required
                                />
                            </div>

                            {/* Type Selection */}
                            <div className="space-y-2">
                                <Label htmlFor="type" className="text-sm font-medium text-foreground flex items-center gap-2">
                                    <Activity className="h-3.5 w-3.5 text-muted-foreground" />
                                    Type
                                </Label>
                                <Select
                                    value={formData.type}
                                    onValueChange={(value) => setFormData({ ...formData, type: value })}
                                >
                                    <SelectTrigger className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background">
                                        <SelectValue placeholder="Select type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="hospital">Hospital</SelectItem>
                                        <SelectItem value="clinic">Clinic</SelectItem>
                                        <SelectItem value="lab">Laboratory</SelectItem>
                                        <SelectItem value="pharmacy">Pharmacy</SelectItem>
                                        <SelectItem value="imaging">Imaging Center</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                {/* Phone */}
                                <div className="space-y-2">
                                    <Label htmlFor="phone" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                                        Phone
                                    </Label>
                                    <Input
                                        id="phone"
                                        value={formData.phone}
                                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        placeholder="+91..."
                                    />
                                </div>
                                {/* Email */}
                                <div className="space-y-2">
                                    <Label htmlFor="email" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <Globe className="h-3.5 w-3.5 text-muted-foreground" />
                                        Email
                                    </Label>
                                    <Input
                                        id="email"
                                        value={formData.email}
                                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        placeholder="contact@org.com"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                {/* City */}
                                <div className="space-y-2">
                                    <Label htmlFor="city" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                                        City
                                    </Label>
                                    <Input
                                        id="city"
                                        value={formData.city}
                                        onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        placeholder="City"
                                    />
                                </div>
                                {/* Country */}
                                <div className="space-y-2">
                                    <Label htmlFor="country" className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <Globe className="h-3.5 w-3.5 text-muted-foreground" />
                                        Country
                                    </Label>
                                    <Input
                                        id="country"
                                        value={formData.country}
                                        onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                                        className="h-11 rounded-xl border-border focus:border-blue-400 focus:ring-blue-400/20 bg-background"
                                        placeholder="Country"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-end gap-3 mt-6 pt-5 border-t border-border">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => setOpen(false)}
                                className="rounded-full px-5 border-border hover:bg-muted"
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                disabled={submitting}
                                className="rounded-full px-6 bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all"
                            >
                                {submitting ? (
                                    <>
                                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                        {editingOrg ? 'Updating...' : 'Saving...'}
                                    </>
                                ) : (
                                    <>
                                        {editingOrg ? <Pencil className="w-4 h-4 mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                                        {editingOrg ? 'Update Organization' : 'Save Organization'}
                                    </>
                                )}
                            </Button>
                        </div>
                    </form>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <DialogContent className="sm:max-w-[500px] p-0 overflow-hidden rounded-2xl border-border">
                    <div className="bg-gradient-to-r from-red-600 to-orange-600 px-6 py-5 text-white">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-white/20 rounded-xl">
                                <AlertTriangle className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <DialogTitle className="text-lg font-semibold text-white">Delete Organization</DialogTitle>
                                <DialogDescription className="text-red-100 text-sm mt-0.5">
                                    This action is permanent and cannot be undone
                                </DialogDescription>
                            </div>
                        </div>
                    </div>

                    <div className="px-6 py-6">
                        <div className="bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/20 rounded-xl p-4 mb-6">
                            <p className="text-sm text-red-800 dark:text-red-300">
                                You are about to delete <span className="font-semibold">{orgToDelete?.name}</span>.
                                All associated data including locations, providers, and patients linked to this organization may be affected.
                            </p>
                        </div>

                        <DialogFooter className="gap-2 sm:gap-0">
                            <Button
                                variant="outline"
                                onClick={() => setDeleteDialogOpen(false)}
                                className="rounded-full px-5 border-border hover:bg-muted"
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="destructive"
                                onClick={confirmDelete}
                                disabled={submitting}
                                className="rounded-full px-5 bg-red-600 hover:bg-red-700 shadow-sm hover:shadow-md transition-all"
                            >
                                {submitting ? (
                                    <>
                                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                        Deleting...
                                    </>
                                ) : (
                                    <>
                                        <Trash2 className="w-4 h-4 mr-2" />
                                        Delete Organization
                                    </>
                                )}
                            </Button>
                        </DialogFooter>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
}
