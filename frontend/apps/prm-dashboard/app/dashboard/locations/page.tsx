'use client';

import { useEffect, useState } from 'react';
import {
    Plus,
    Search,
    MapPin,
    Building2,
    CheckCircle2,
    XCircle,
    Building,
    MoreHorizontal,
    Pencil,
    LayoutGrid,
    Bed,
    Stethoscope
} from 'lucide-react';
import { toast } from 'react-hot-toast';

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
    getLocations,
    createLocation,
    updateLocation
} from '@/lib/api/locations';
import { getOrganizations } from '@/lib/api/organizations';
import { Location, Organization } from '@/lib/api/types';

export default function LocationsPage() {
    const [loading, setLoading] = useState(true);
    const [locations, setLocations] = useState<Location[]>([]);
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [searchQuery, setSearchQuery] = useState('');

    // Dialog State
    const [open, setOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Edit State
    const [editingLocation, setEditingLocation] = useState<Location | null>(null);

    const [formData, setFormData] = useState({
        name: '',
        type: 'department',
        code: '',
        building: '',
        floor: '',
        room: '',
        organization_id: '',
        is_active: true
    });

    const fetchData = async () => {
        setLoading(true);
        // Fetch locations and organizations in parallel
        const [locationsRes, orgsRes] = await Promise.all([
            getLocations({ page: 1, page_size: 100 }),
            getOrganizations({ page: 1, page_size: 100 })
        ]);

        const [locData, locError] = locationsRes;
        const [orgData, orgError] = orgsRes;

        if (locError) {
            console.error('Failed to fetch locations:', locError);
            toast.error('Failed to load locations');
        } else if (locData) {
            setLocations(locData.items);
        }

        if (orgError) {
            console.error('Failed to fetch organizations:', orgError);
        } else if (orgData) {
            setOrganizations(orgData.items);
        }

        setLoading(false);
    };

    useEffect(() => {
        fetchData();
    }, []);

    // Reset form when dialog closes
    useEffect(() => {
        if (!open) {
            setEditingLocation(null);
            setFormData({
                name: '',
                type: 'department',
                code: '',
                building: '',
                floor: '',
                room: '',
                organization_id: '',
                is_active: true
            });
        }
    }, [open]);

    const handleEdit = (loc: Location) => {
        setEditingLocation(loc);
        setFormData({
            name: loc.name,
            type: loc.type || 'department',
            code: loc.code || '',
            building: loc.building || '',
            floor: loc.floor || '',
            room: loc.room || '',
            organization_id: loc.organization_id || '',
            is_active: loc.is_active
        });
        setOpen(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name) {
            toast.error('Location Name is required');
            return;
        }

        setSubmitting(true);

        let error;
        let result;

        const payload = {
            ...formData,
            // Convert empty strings to undefined if needed, or keeping them as empty string is fine for some inputs
            // Ensure tenant_id is set for new records (mocked for now)
            tenant_id: '00000000-0000-0000-0000-000000000001',
        };

        if (editingLocation) {
            // Update
            [result, error] = await updateLocation(editingLocation.id, payload);
        } else {
            // Create
            [result, error] = await createLocation(payload);
        }

        if (error) {
            console.error(`Failed to ${editingLocation ? 'update' : 'create'} location:`, error);
            toast.error(error.message || `Failed to ${editingLocation ? 'update' : 'create'} location`);
        } else if (result) {
            toast.success(`Location ${editingLocation ? 'updated' : 'created'} successfully`);
            setOpen(false);
            fetchData();
        }
        setSubmitting(false);
    };

    const filteredLocations = locations.filter(loc =>
        loc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (loc.code && loc.code.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (loc.building && loc.building.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    // Calculate Stats
    const stats = {
        total: locations.length,
        active: locations.filter(l => l.is_active).length,
        departments: locations.filter(l => l.type?.toLowerCase().includes('department')).length,
        clinics: locations.filter(l => l.type?.toLowerCase().includes('clinic')).length,
        wards: locations.filter(l => l.type?.toLowerCase().includes('ward')).length,
        inactive: locations.filter(l => !l.is_active).length
    };

    return (
        <div className="space-y-8 pb-10">
            {/* Flat Header */}
            <div className="flex items-center justify-between sticky top-[4rem] z-20 bg-white dark:bg-gray-900 py-4 -mx-6 px-6 border-b-2 border-gray-100 dark:border-gray-800">
                <div>
                    <h1 className="text-2xl font-heading text-gray-900 dark:text-white">Locations</h1>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Manage physical spaces, rooms, and beds</p>
                </div>
                <Button
                    onClick={() => setOpen(true)}
                    className="flat-btn-primary"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    New Location
                </Button>
            </div>

            {/* Flat Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Total</span>
                        <MapPin className="w-5 h-5 text-blue-500" />
                    </div>
                    <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.total}</div>
                    <p className="text-xs text-gray-500 mt-1">Stored Locations</p>
                </div>

                <div className="bg-emerald-50 dark:bg-emerald-900/20 border-2 border-emerald-200 dark:border-emerald-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Active</span>
                        <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    </div>
                    <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{stats.active}</div>
                    <p className="text-xs text-emerald-600 mt-1">In Use</p>
                </div>

                <div className="bg-indigo-50 dark:bg-indigo-900/20 border-2 border-indigo-200 dark:border-indigo-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Departments</span>
                        <LayoutGrid className="w-5 h-5 text-indigo-500" />
                    </div>
                    <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">{stats.departments}</div>
                    <p className="text-xs text-indigo-600 mt-1">Medical Units</p>
                </div>

                <div className="bg-teal-50 dark:bg-teal-900/20 border-2 border-teal-200 dark:border-teal-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Clinics</span>
                        <Stethoscope className="w-5 h-5 text-teal-500" />
                    </div>
                    <div className="text-3xl font-bold text-teal-600 dark:text-teal-400">{stats.clinics}</div>
                    <p className="text-xs text-teal-600 mt-1">OPD Rooms</p>
                </div>

                <div className="bg-amber-50 dark:bg-amber-900/20 border-2 border-amber-200 dark:border-amber-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Wards</span>
                        <Bed className="w-5 h-5 text-amber-500" />
                    </div>
                    <div className="text-3xl font-bold text-amber-600 dark:text-amber-400">{stats.wards}</div>
                    <p className="text-xs text-amber-600 mt-1">Inpatient</p>
                </div>

                <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Inactive</span>
                        <XCircle className="w-5 h-5 text-red-500" />
                    </div>
                    <div className="text-3xl font-bold text-red-600 dark:text-red-400">{stats.inactive}</div>
                    <p className="text-xs text-red-500 mt-1">Closed/Maint</p>
                </div>
            </div>

            {/* Main Content */}
            <Card className="border-border shadow-sm">
                <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <CardTitle>Locations Directory</CardTitle>
                            <p className="text-sm text-muted-foreground">
                                All physical locations defined in the system.
                            </p>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="mb-6 flex flex-col sm:flex-row items-center gap-4">
                        <div className="relative flex-1 w-full">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search by name, code, building..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 h-10 rounded-xl bg-muted/30 border-border md:w-[350px]"
                            />
                        </div>
                    </div>

                    <div className="rounded-xl border border-border overflow-hidden">
                        <Table>
                            <TableHeader className="bg-muted/50">
                                <TableRow>
                                    <TableHead className="font-semibold">Name</TableHead>
                                    <TableHead className="font-semibold">Type</TableHead>
                                    <TableHead className="font-semibold">Location</TableHead>
                                    <TableHead className="font-semibold">Organization</TableHead>
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
                                ) : filteredLocations.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                                            No locations found matching your search.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredLocations.map((loc) => (
                                        <TableRow key={loc.id} className="group hover:bg-muted/50 transition-colors">
                                            <TableCell className="font-medium">
                                                <div className="flex items-center gap-2">
                                                    <div className="p-1.5 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
                                                        <MapPin className="h-4 w-4" />
                                                    </div>
                                                    <div>
                                                        <div className="font-medium">{loc.name}</div>
                                                        {loc.code && <div className="text-xs text-muted-foreground">{loc.code}</div>}
                                                    </div>
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="secondary" className="capitalize font-medium rounded-md">
                                                    {loc.type}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <div className="text-sm text-muted-foreground">
                                                    {loc.building && <span>{loc.building}</span>}
                                                    {loc.floor && <span>, Floor {loc.floor}</span>}
                                                    {loc.room && <span>, Room {loc.room}</span>}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                {organizations.find(o => o.id === loc.organization_id)?.name || '-'}
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    className={
                                                        loc.is_active
                                                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 hover:bg-green-100'
                                                            : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 hover:bg-red-100'
                                                    }
                                                >
                                                    {loc.is_active ? 'Active' : 'Inactive'}
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
                                                        <DropdownMenuItem onClick={() => handleEdit(loc)}>
                                                            <Pencil className="mr-2 h-4 w-4" />
                                                            Edit Details
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

            {/* Create/Edit Dialog */}
            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent className="sm:max-w-[600px] p-0 overflow-hidden rounded-lg border-2 border-gray-200 dark:border-gray-700">
                    <div className="bg-blue-600 px-6 py-5 text-white border-b-2 border-blue-700">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-white/20 rounded-lg border-2 border-white/30">
                                <MapPin className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <DialogTitle className="text-lg font-heading text-white">
                                    {editingLocation ? 'Edit Location' : 'Add New Location'}
                                </DialogTitle>
                                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                                    {editingLocation ? 'Update location details' : 'Define a new physical space in the system'}
                                </DialogDescription>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="px-6 py-5">
                        <div className="grid grid-cols-2 gap-5">
                            {/* Name */}
                            <div className="space-y-2 col-span-2">
                                <Label htmlFor="name" className="text-sm font-medium flex items-center gap-2">
                                    Location Name <span className="text-red-500">*</span>
                                </Label>
                                <Input
                                    id="name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="h-11 rounded-xl"
                                    placeholder="e.g. Ward A, Room 101"
                                    required
                                />
                            </div>

                            {/* Type */}
                            <div className="space-y-2">
                                <Label htmlFor="type" className="text-sm font-medium">Type</Label>
                                <Select
                                    value={formData.type}
                                    onValueChange={(value) => setFormData({ ...formData, type: value })}
                                >
                                    <SelectTrigger className="h-11 rounded-xl">
                                        <SelectValue placeholder="Select Type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="department">Department</SelectItem>
                                        <SelectItem value="clinic">Clinic</SelectItem>
                                        <SelectItem value="ward">Ward</SelectItem>
                                        <SelectItem value="room">Room</SelectItem>
                                        <SelectItem value="bed">Bed</SelectItem>
                                        <SelectItem value="building">Building</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Code */}
                            <div className="space-y-2">
                                <Label htmlFor="code" className="text-sm font-medium">Code/Identifier</Label>
                                <Input
                                    id="code"
                                    value={formData.code}
                                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                                    className="h-11 rounded-xl"
                                    placeholder="e.g. WARD-A"
                                />
                            </div>

                            {/* Organization */}
                            <div className="space-y-2 col-span-2">
                                <Label htmlFor="org" className="text-sm font-medium">Organization</Label>
                                <Select
                                    value={formData.organization_id}
                                    onValueChange={(value) => setFormData({ ...formData, organization_id: value })}
                                >
                                    <SelectTrigger className="h-11 rounded-xl">
                                        <SelectValue placeholder="Select Organization" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {organizations.map(org => (
                                            <SelectItem key={org.id} value={org.id}>{org.name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Building */}
                            <div className="space-y-2">
                                <Label htmlFor="building" className="text-sm font-medium">Building</Label>
                                <Input
                                    id="building"
                                    value={formData.building}
                                    onChange={(e) => setFormData({ ...formData, building: e.target.value })}
                                    className="h-11 rounded-xl"
                                    placeholder="Main Wing"
                                />
                            </div>

                            {/* Floor */}
                            <div className="space-y-2">
                                <Label htmlFor="floor" className="text-sm font-medium">Floor</Label>
                                <Input
                                    id="floor"
                                    value={formData.floor}
                                    onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
                                    className="h-11 rounded-xl"
                                    placeholder="e.g. 2nd Floor"
                                />
                            </div>

                            {/* Room */}
                            <div className="space-y-2">
                                <Label htmlFor="room" className="text-sm font-medium">Room</Label>
                                <Input
                                    id="room"
                                    value={formData.room}
                                    onChange={(e) => setFormData({ ...formData, room: e.target.value })}
                                    className="h-11 rounded-xl"
                                    placeholder="e.g. 204"
                                />
                            </div>

                            {/* Status */}
                            <div className="space-y-2 flex items-center justify-between pt-8">
                                <Label htmlFor="is_active" className="text-sm font-medium">Active Status</Label>
                                <div className="flex items-center gap-2">
                                    <span className={`text-sm ${formData.is_active ? 'text-green-600' : 'text-muted-foreground'}`}>
                                        {formData.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                    <Button
                                        type="button"
                                        variant={formData.is_active ? 'default' : 'outline'}
                                        size="sm"
                                        onClick={() => setFormData({ ...formData, is_active: !formData.is_active })}
                                        className={formData.is_active ? 'bg-green-600 hover:bg-green-700' : ''}
                                    >
                                        {formData.is_active ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                                    </Button>
                                </div>
                            </div>
                        </div>

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
                                        {editingLocation ? 'Updating...' : 'Saving...'}
                                    </>
                                ) : (
                                    <>
                                        {editingLocation ? <Pencil className="w-4 h-4 mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                                        {editingLocation ? 'Update Location' : 'Save Location'}
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
