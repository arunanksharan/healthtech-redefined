'use client';

import { useEffect, useState } from 'react';
import {
    Plus,
    Search,
    Calendar,
    User,
    Stethoscope,
    Clock,
    CheckCircle2,
    XCircle,
    MoreHorizontal,
    Pencil,
    Activity,
    Users
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { format } from 'date-fns';

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
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import {
    getEncounters,
    createEncounter,
    updateEncounter
} from '@/lib/api/encounters';
import { patientsAPI } from '@/lib/api/patients';
import { practitionersAPI } from '@/lib/api/practitioners';
import { Encounter } from '@/lib/api/types';
import { Patient } from '@/lib/types'; // Import from types as used in patientsAPI
import { Practitioner } from '@/lib/api/practitioners';
import { PatientCombobox } from '@/components/dashboard/patient-combobox';

export default function EncountersPage() {
    const [loading, setLoading] = useState(true);
    const [encounters, setEncounters] = useState<Encounter[]>([]);
    const [patients, setPatients] = useState<Patient[]>([]);
    const [practitioners, setPractitioners] = useState<Practitioner[]>([]);
    const [searchQuery, setSearchQuery] = useState('');

    // Dialog State
    const [open, setOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Edit State
    const [editingEncounter, setEditingEncounter] = useState<Encounter | null>(null);

    const [formData, setFormData] = useState({
        patient_id: '',
        practitioner_id: '',
        status: 'planned',
        class_code: 'AMB',
        started_at: '',
        ended_at: ''
    });

    const fetchData = async () => {
        setLoading(true);
        try {
            const [encountersRes, patientsRes, practitionersRes] = await Promise.all([
                getEncounters({ page: 1, page_size: 100 }),
                patientsAPI.getAll({ page_size: 100 }),
                practitionersAPI.getAll({ page_size: 100 })
            ]);

            const [encData, encError] = encountersRes;
            const [patData, patError] = patientsRes;
            const [pracData, pracError] = practitionersRes;

            if (encError) {
                console.error('Failed to fetch encounters:', encError);
                toast.error('Failed to load encounters');
            } else if (encData) {
                setEncounters(encData.items);
            }

            if (patData) setPatients(patData.items);
            if (pracData) setPractitioners(pracData.items);

        } catch (error) {
            console.error('Error fetching data:', error);
            toast.error('Failed to load data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        if (!open) {
            setEditingEncounter(null);
            setFormData({
                patient_id: '',
                practitioner_id: '',
                status: 'planned',
                class_code: 'AMB',
                started_at: '',
                ended_at: ''
            });
        }
    }, [open]);

    const handleEdit = (enc: Encounter) => {
        setEditingEncounter(enc);
        setFormData({
            patient_id: enc.patient_id,
            practitioner_id: enc.practitioner_id,
            status: enc.status,
            class_code: enc.class_code,
            started_at: enc.started_at ? enc.started_at.split('.')[0] : '', // Simple ISO handling
            ended_at: enc.ended_at ? enc.ended_at.split('.')[0] : ''
        });
        setOpen(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.patient_id || !formData.practitioner_id) {
            toast.error('Patient and Practitioner are required');
            return;
        }

        setSubmitting(true);

        let error;
        let result;

        const payload = {
            ...formData,
            tenant_id: '00000000-0000-0000-0000-000000000001',
            // Only send dates if they are present
            started_at: formData.started_at || undefined,
            ended_at: formData.ended_at || undefined
        };

        if (editingEncounter) {
            [result, error] = await updateEncounter(editingEncounter.id, payload);
        } else {
            [result, error] = await createEncounter(payload);
        }

        if (error) {
            console.error(`Failed to ${editingEncounter ? 'update' : 'create'} encounter:`, error);
            toast.error(error.message || `Failed to ${editingEncounter ? 'update' : 'create'} encounter`);
        } else if (result) {
            toast.success(`Encounter ${editingEncounter ? 'updated' : 'created'} successfully`);
            setOpen(false);
            fetchData();
        }
        setSubmitting(false);
    };

    // Helper to look up names
    const getPatientName = (id: string) => {
        const p = patients.find(p => p.id === id);
        return p ? `${p.first_name} ${p.last_name}` : 'Unknown Patient';
    };

    const getPractitionerName = (id: string) => {
        const p = practitioners.find(p => p.id === id);
        return p ? `Dr. ${p.first_name} ${p.last_name}` : 'Unknown Practitioner';
    };

    const filteredEncounters = encounters.filter(enc =>
        getPatientName(enc.patient_id).toLowerCase().includes(searchQuery.toLowerCase()) ||
        enc.status.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const stats = {
        total: encounters.length,
        planned: encounters.filter(e => e.status === 'planned').length,
        inProgress: encounters.filter(e => e.status === 'in-progress').length,
        completed: encounters.filter(e => e.status === 'completed').length,
        cancelled: encounters.filter(e => e.status === 'cancelled').length
    };

    return (
        <div className="space-y-8 pb-10">
            {/* Header */}
            <div className="flex items-center justify-between sticky top-[4rem] z-20 bg-background/90 backdrop-blur-md py-4 -mx-6 px-6 border-b border-border/50">
                <div>
                    <h1 className="text-2xl font-bold text-foreground tracking-tight">Encounters</h1>
                    <p className="text-muted-foreground text-sm">Patient visits and interactions</p>
                </div>
                <Button
                    onClick={() => setOpen(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all rounded-full px-6"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    New Encounter
                </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--primary) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Total</CardTitle>
                        <Activity className="w-4 h-4 text-primary" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.total}</div>
                        <p className="text-xs text-muted-foreground mt-1">All Visits</p>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--info) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Planned</CardTitle>
                        <Calendar className="w-4 h-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.planned}</div>
                        <p className="text-xs text-blue-500 mt-1 font-medium">Scheduled</p>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--warning) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">In Progress</CardTitle>
                        <Clock className="w-4 h-4 text-yellow-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.inProgress}</div>
                        <p className="text-xs text-yellow-500 mt-1 font-medium">Ongoing</p>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--success) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Completed</CardTitle>
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.completed}</div>
                        <p className="text-xs text-green-500 mt-1 font-medium">Finished</p>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--destructive) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Cancelled</CardTitle>
                        <XCircle className="w-4 h-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.cancelled}</div>
                        <p className="text-xs text-red-500 mt-1 font-medium">Did Not Occur</p>
                    </CardContent>
                </MagicCard>
            </div>

            {/* List */}
            <Card className="border-border shadow-sm">
                <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <CardTitle>Encounter History</CardTitle>
                            <p className="text-sm text-muted-foreground">
                                Detailed log of patient interactions and visits.
                            </p>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="mb-6 flex flex-col sm:flex-row items-center gap-4">
                        <div className="relative flex-1 w-full">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search by patient name or status..."
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
                                    <TableHead className="font-semibold">Patient</TableHead>
                                    <TableHead className="font-semibold">Practitioner</TableHead>
                                    <TableHead className="font-semibold">Type</TableHead>
                                    <TableHead className="font-semibold">Status</TableHead>
                                    <TableHead className="font-semibold">Date</TableHead>
                                    <TableHead className="w-[80px]">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    Array.from({ length: 5 }).map((_, i) => (
                                        <TableRow key={i}>
                                            <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[80px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[80px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[120px]" /></TableCell>
                                            <TableCell><Skeleton className="h-8 w-8 rounded-full" /></TableCell>
                                        </TableRow>
                                    ))
                                ) : filteredEncounters.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                                            No encounters found matching your search.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredEncounters.map((enc) => (
                                        <TableRow key={enc.id} className="group hover:bg-muted/50 transition-colors">
                                            <TableCell className="font-medium">
                                                <div className="flex items-center gap-2">
                                                    <div className="p-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                                                        <User className="h-4 w-4" />
                                                    </div>
                                                    {getPatientName(enc.patient_id)}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2 text-muted-foreground">
                                                    <Stethoscope className="h-3.5 w-3.5" />
                                                    {getPractitionerName(enc.practitioner_id)}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline">{enc.class_code}</Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant="secondary"
                                                    className={
                                                        enc.status === 'completed' ? 'bg-green-100 text-green-700' :
                                                            enc.status === 'in-progress' ? 'bg-yellow-100 text-yellow-700' :
                                                                enc.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                                                                    'bg-blue-100 text-blue-700'
                                                    }
                                                >
                                                    {enc.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground text-sm">
                                                {enc.started_at ? format(new Date(enc.started_at), 'PP p') : '-'}
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
                                                        <DropdownMenuItem onClick={() => handleEdit(enc)}>
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

            {/* Dialog */}
            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent className="sm:max-w-[600px] p-0 overflow-hidden rounded-2xl border-border">
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5 text-white">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-white/20 rounded-xl">
                                <Activity className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <DialogTitle className="text-lg font-semibold text-white">
                                    {editingEncounter ? 'Edit Encounter' : 'New Encounter'}
                                </DialogTitle>
                                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                                    {editingEncounter ? 'Update encounter status and details' : 'Log a new patient visit or interaction'}
                                </DialogDescription>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="px-6 py-5">
                        <div className="grid grid-cols-2 gap-5">
                            {/* Patient */}
                            <div className="space-y-2 col-span-2">
                                <Label htmlFor="patient" className="text-sm font-medium flex items-center gap-2">
                                    Patient <span className="text-red-500">*</span>
                                </Label>
                                <PatientCombobox
                                    value={formData.patient_id}
                                    onChange={(value) => setFormData({ ...formData, patient_id: value })}
                                    patients={patients}
                                    error={!formData.patient_id && submitting}
                                />
                            </div>

                            {/* Practitioner */}
                            <div className="space-y-2 col-span-2">
                                <Label htmlFor="practitioner" className="text-sm font-medium flex items-center gap-2">
                                    Practitioner <span className="text-red-500">*</span>
                                </Label>
                                <Select
                                    value={formData.practitioner_id}
                                    onValueChange={(value) => setFormData({ ...formData, practitioner_id: value })}
                                >
                                    <SelectTrigger className="h-11 rounded-xl">
                                        <SelectValue placeholder="Select Practitioner" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {practitioners.map(p => (
                                            <SelectItem key={p.id} value={p.id}>Dr. {p.first_name} {p.last_name} - {p.speciality}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Status */}
                            <div className="space-y-2">
                                <Label htmlFor="status" className="text-sm font-medium">Status <span className="text-red-500">*</span></Label>
                                <Select
                                    value={formData.status}
                                    onValueChange={(value) => setFormData({ ...formData, status: value })}
                                >
                                    <SelectTrigger className="h-11 rounded-xl">
                                        <SelectValue placeholder="Status" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="planned">Planned</SelectItem>
                                        <SelectItem value="in-progress">In Progress</SelectItem>
                                        <SelectItem value="completed">Completed</SelectItem>
                                        <SelectItem value="cancelled">Cancelled</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Type */}
                            <div className="space-y-2">
                                <Label htmlFor="class_code" className="text-sm font-medium">Class (Type) <span className="text-red-500">*</span></Label>
                                <Select
                                    value={formData.class_code}
                                    onValueChange={(value) => setFormData({ ...formData, class_code: value })}
                                >
                                    <SelectTrigger className="h-11 rounded-xl">
                                        <SelectValue placeholder="Class Code" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="AMB">Ambulatory (Outpatient)</SelectItem>
                                        <SelectItem value="IMP">Inpatient</SelectItem>
                                        <SelectItem value="EMER">Emergency</SelectItem>
                                        <SelectItem value="HH">Home Health</SelectItem>
                                    </SelectContent>
                                </Select>
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
                                        {editingEncounter ? 'Updating...' : 'Saving...'}
                                    </>
                                ) : (
                                    <>
                                        {editingEncounter ? <Pencil className="w-4 h-4 mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                                        {editingEncounter ? 'Update Encounter' : 'Save Encounter'}
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
