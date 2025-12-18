'use client';

import { useEffect, useState } from 'react';
import {
    Plus,
    Search,
    Pill,
    User,
    Calendar,
    CheckCircle2,
    XCircle,
    Activity,
    MoreHorizontal,
    FileText,
    Syringe
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

import { getMedications, createMedication } from '@/lib/api/medications';
import { patientsAPI } from '@/lib/api/patients';
import { Medication } from '@/lib/api/types';
import { Patient } from '@/lib/types';
import { PatientCombobox } from '@/components/dashboard/patient-combobox';

// Common Medications for Quick Select
const COMMON_MEDS = [
    { code: 'aspirin', label: 'Aspirin', system: 'RxNorm' },
    { code: 'lisinopril', label: 'Lisinopril', system: 'RxNorm' },
    { code: 'metformin', label: 'Metformin', system: 'RxNorm' },
    { code: 'atorvastatin', label: 'Atorvastatin', system: 'RxNorm' },
    { code: 'amoxicillin', label: 'Amoxicillin', system: 'RxNorm' },
];

export default function MedicationsPage() {
    const [loading, setLoading] = useState(true);
    const [medications, setMedications] = useState<Medication[]>([]);
    const [patients, setPatients] = useState<Patient[]>([]);
    const [searchQuery, setSearchQuery] = useState('');

    // Dialog State
    const [open, setOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    const [formData, setFormData] = useState({
        patient_id: '',
        status: 'active',
        intent: 'order',
        medication_code: '',
        medication_display: '',
        dosage_text: '',
        note: ''
    });

    const [selectedCommon, setSelectedCommon] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [medRes, patRes] = await Promise.all([
                getMedications({ page: 1, page_size: 100 }),
                patientsAPI.getAll({ page_size: 100 })
            ]);

            const [medData, medError] = medRes;
            const [patData, patError] = patRes;

            if (medError) {
                console.error('Failed to fetch medications:', medError);
                toast.error('Failed to load medications');
            } else if (medData) {
                setMedications(medData.items);
            }

            if (patData) setPatients(patData.items);

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

    // Reset form when opening dialog
    useEffect(() => {
        if (!open) {
            setFormData({
                patient_id: '',
                status: 'active',
                intent: 'order',
                medication_code: '',
                medication_display: '',
                dosage_text: '',
                note: ''
            });
            setSelectedCommon(null);
        }
    }, [open]);

    // Handle Quick Select
    useEffect(() => {
        if (selectedCommon) {
            const med = COMMON_MEDS.find(m => m.code === selectedCommon);
            if (med) {
                setFormData(prev => ({
                    ...prev,
                    medication_code: med.code,
                    medication_display: med.label
                }));
            }
        }
    }, [selectedCommon]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.patient_id || !formData.medication_display) {
            toast.error('Patient and Medication Name are required');
            return;
        }

        setSubmitting(true);

        const payload: Partial<Medication> = {
            patient_id: formData.patient_id,
            status: formData.status,
            intent: formData.intent,
            tenant_id: '00000000-0000-0000-0000-000000000001',
            medication: {
                system: 'http://www.nlm.nih.gov/research/umls/rxnorm', // Default system
                code: formData.medication_code || formData.medication_display.toLowerCase().replace(/\s+/g, '-'),
                display: formData.medication_display
            },
            dosage: formData.dosage_text ? {
                text: formData.dosage_text
            } : undefined,
            note: formData.note || undefined,
            authored_on: new Date().toISOString()
        };

        const [result, error] = await createMedication(payload);

        if (error) {
            console.error(`Failed to prescribe medication:`, error);
            toast.error(error.message || `Failed to prescribe medication`);
        } else if (result) {
            toast.success(`Medication prescribed successfully`);
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

    const filteredMeds = medications.filter(m =>
        getPatientName(m.patient_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.medication.display?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const stats = {
        total: medications.length,
        active: medications.filter(m => m.status === 'active').length,
        completed: medications.filter(m => m.status === 'completed' || m.status === 'stopped').length,
    };

    return (
        <div className="space-y-8 pb-10">
            {/* Flat Header */}
            <div className="flex items-center justify-between sticky top-[4rem] z-20 bg-white dark:bg-gray-900 py-4 -mx-6 px-6 border-b-2 border-gray-100 dark:border-gray-800">
                <div>
                    <h1 className="text-2xl font-heading text-gray-900 dark:text-white">Medications</h1>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Patient prescriptions and medication history</p>
                </div>
                <Button
                    onClick={() => setOpen(true)}
                    className="flat-btn-primary"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    Prescribe Medication
                </Button>
            </div>

            {/* Flat Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Prescriptions</span>
                        <Pill className="w-5 h-5 text-blue-500" />
                    </div>
                    <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.total}</div>
                </div>

                <div className="bg-emerald-50 dark:bg-emerald-900/20 border-2 border-emerald-200 dark:border-emerald-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Active</span>
                        <Activity className="w-5 h-5 text-emerald-500" />
                    </div>
                    <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{stats.active}</div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Completed/Stopped</span>
                        <CheckCircle2 className="w-5 h-5 text-gray-500" />
                    </div>
                    <div className="text-3xl font-bold text-gray-600 dark:text-gray-400">{stats.completed}</div>
                </div>
            </div>

            {/* List */}
            <Card className="border-border shadow-sm">
                <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <CardTitle>Medication List</CardTitle>
                            <p className="text-sm text-muted-foreground">
                                Detailed log of prescribed medications.
                            </p>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="mb-6 flex flex-col sm:flex-row items-center gap-4">
                        <div className="relative flex-1 w-full">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search by patient or medication..."
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
                                    <TableHead className="font-semibold">Medication</TableHead>
                                    <TableHead className="font-semibold">Status</TableHead>
                                    <TableHead className="font-semibold">Dosage</TableHead>
                                    <TableHead className="font-semibold">Prescribed On</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    Array.from({ length: 5 }).map((_, i) => (
                                        <TableRow key={i}>
                                            <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[80px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[120px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[100px]" /></TableCell>
                                        </TableRow>
                                    ))
                                ) : filteredMeds.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-32 text-center text-muted-foreground">
                                            No medications found.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredMeds.map((med) => (
                                        <TableRow key={med.id} className="group hover:bg-muted/50 transition-colors">
                                            <TableCell className="font-medium">
                                                <div className="flex items-center gap-2">
                                                    <div className="p-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                                                        <User className="h-4 w-4" />
                                                    </div>
                                                    {getPatientName(med.patient_id || '')}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <div className="font-medium">{med.medication.display}</div>
                                                <div className="text-xs text-muted-foreground">{med.medication.code}</div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant="secondary"
                                                    className={
                                                        med.status === 'active' ? 'bg-green-100 text-green-700' :
                                                            med.status === 'stopped' ? 'bg-red-100 text-red-700' :
                                                                'bg-gray-100 text-gray-700'
                                                    }
                                                >
                                                    {med.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground text-sm">
                                                {med.dosage?.text || '-'}
                                            </TableCell>
                                            <TableCell className="text-muted-foreground text-sm">
                                                {med.authored_on ? format(new Date(med.authored_on), 'PP') : '-'}
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
                <DialogContent className="sm:max-w-[600px] p-0 overflow-hidden rounded-lg border-2 border-gray-200 dark:border-gray-700">
                    <div className="bg-blue-600 px-6 py-5 text-white border-b-2 border-blue-700">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-white/20 rounded-lg border-2 border-white/30">
                                <Pill className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <DialogTitle className="text-lg font-heading text-white">Prescribe Medication</DialogTitle>
                                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                                    Add a new medication order for the patient
                                </DialogDescription>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
                        {/* Patient */}
                        <div className="space-y-2">
                            <Label htmlFor="patient" className="text-sm font-medium">Patient <span className="text-red-500">*</span></Label>
                            <PatientCombobox
                                value={formData.patient_id}
                                onChange={(value) => setFormData({ ...formData, patient_id: value })}
                                patients={patients}
                                error={!formData.patient_id && submitting}
                            />
                        </div>

                        {/* Quick Select */}
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Common Medications</Label>
                            <div className="flex flex-wrap gap-2">
                                {COMMON_MEDS.map((m) => (
                                    <Badge
                                        key={m.code}
                                        variant="outline"
                                        className={`cursor-pointer px-3 py-1.5 transition-colors ${selectedCommon === m.code ? 'bg-blue-50 border-blue-500 text-blue-700' : 'hover:bg-muted'}`}
                                        onClick={() => setSelectedCommon(m.code)}
                                    >
                                        {m.label}
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        {/* Medication Details */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2 col-span-2">
                                <Label htmlFor="medication" className="text-sm font-medium">Medication Name <span className="text-red-500">*</span></Label>
                                <Input
                                    placeholder="e.g. Ibuprofen 400mg"
                                    value={formData.medication_display}
                                    onChange={(e) => setFormData({ ...formData, medication_display: e.target.value })}
                                    className="h-11 rounded-xl"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="status" className="text-sm font-medium">Status</Label>
                                <Select
                                    value={formData.status}
                                    onValueChange={(value) => setFormData({ ...formData, status: value })}
                                >
                                    <SelectTrigger className="h-11 rounded-xl">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="active">Active</SelectItem>
                                        <SelectItem value="completed">Completed</SelectItem>
                                        <SelectItem value="stopped">Stopped</SelectItem>
                                        <SelectItem value="on-hold">On Hold</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="dosage" className="text-sm font-medium">Dosage Instructions</Label>
                                <Input
                                    placeholder="e.g. 1 tab daily with food"
                                    value={formData.dosage_text}
                                    onChange={(e) => setFormData({ ...formData, dosage_text: e.target.value })}
                                    className="h-11 rounded-xl"
                                />
                            </div>
                        </div>

                        {/* Note */}
                        <div className="space-y-2">
                            <Label htmlFor="note" className="text-sm font-medium">Notes</Label>
                            <Input
                                placeholder="Additional instructions..."
                                value={formData.note}
                                onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                                className="h-11 rounded-xl"
                            />
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-end gap-3 pt-4 border-t border-border mt-2">
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
                                {submitting ? 'Prescribing...' : 'Prescribe'}
                            </Button>
                        </div>
                    </form>
                </DialogContent>
            </Dialog>
        </div>
    );
}
