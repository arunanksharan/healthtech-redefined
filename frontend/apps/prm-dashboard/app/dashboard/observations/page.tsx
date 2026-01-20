'use client';

import { useEffect, useState } from 'react';
import {
    Plus,
    Search,
    Activity,
    FileText,
    AlertCircle,
    CheckCircle2,
    Thermometer,
    Heart,
    Scale,
    Droplets
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
    getObservations,
    createObservation,
    CreateObservationData
} from '@/lib/api/observations';
import { patientsAPI } from '@/lib/api/patients';
import { Observation } from '@/lib/api/types';
import { Patient } from '@/lib/types';
import { PatientCombobox } from '@/components/dashboard/patient-combobox';

// Common Observation Types Helpers
const COMMON_OBSERVATIONS = [
    { label: 'Heart Rate', code: '8867-4', system: 'http://loinc.org', unit: 'beats/min', icon: Heart },
    { label: 'Body Temperature', code: '8310-5', system: 'http://loinc.org', unit: '°C', icon: Thermometer },
    { label: 'Body Weight', code: '29463-7', system: 'http://loinc.org', unit: 'kg', icon: Scale },
    { label: 'Blood Pressure (Systolic)', code: '8480-6', system: 'http://loinc.org', unit: 'mmHg', icon: Droplets },
    { label: 'Blood Pressure (Diastolic)', code: '8462-4', system: 'http://loinc.org', unit: 'mmHg', icon: Droplets },
    { label: 'Respiratory Rate', code: '9279-1', system: 'http://loinc.org', unit: 'breaths/min', icon: Activity },
    { label: 'Oxygen Saturation', code: '2708-6', system: 'http://loinc.org', unit: '%', icon: Activity },
];

export default function ObservationsPage() {
    const [loading, setLoading] = useState(true);
    const [observations, setObservations] = useState<Observation[]>([]);
    const [patients, setPatients] = useState<Patient[]>([]);
    const [searchQuery, setSearchQuery] = useState('');

    // Dialog State
    const [open, setOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Form State
    const [selectedType, setSelectedType] = useState<string>(''); // code
    const [formData, setFormData] = useState({
        patient_id: '',
        status: 'final',
        category: 'vital-signs',
        value: '',
        note: ''
    });

    const fetchData = async () => {
        setLoading(true);
        try {
            const [obsRes, patRes] = await Promise.all([
                getObservations({ page: 1, page_size: 100 }),
                patientsAPI.getAll({ page_size: 100 })
            ]);

            const [obsData, obsError] = obsRes;
            const [patData, patError] = patRes;

            if (obsError) {
                console.error('Failed to fetch observations:', obsError);
                toast.error('Failed to load observations');
            } else if (obsData) {
                setObservations(obsData.items);
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

    // Reset form when dialog closes
    useEffect(() => {
        if (!open) {
            setSelectedType('');
            setFormData({
                patient_id: '',
                status: 'final',
                category: 'vital-signs',
                value: '',
                note: ''
            });
        }
    }, [open]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.patient_id || !selectedType || !formData.value) {
            toast.error('Please fill in all required fields');
            return;
        }

        const typeDef = COMMON_OBSERVATIONS.find(t => t.code === selectedType);
        if (!typeDef) return;

        setSubmitting(true);

        const payload: CreateObservationData = {
            tenant_id: '00000000-0000-0000-0000-000000000001',
            patient_id: formData.patient_id,
            status: formData.status,
            category: formData.category,
            code: {
                system: typeDef.system,
                code: typeDef.code,
                display: typeDef.label
            },
            value: {
                value: parseFloat(formData.value),
                unit: typeDef.unit,
                system: 'http://unitsofmeasure.org',
                code: typeDef.unit
            },
            note: formData.note,
            effective_datetime: new Date().toISOString()
        };

        const [result, error] = await createObservation(payload);

        if (error) {
            console.error('Failed to create observation:', error);
            toast.error(error.message || 'Failed to create observation');
        } else if (result) {
            toast.success('Observation recorded successfully');
            setOpen(false);
            fetchData();
        }
        setSubmitting(false);
    };

    const getPatientName = (id: string) => {
        const p = patients.find(p => p.id === id);
        return p ? `${p.first_name} ${p.last_name}` : 'Unknown Patient';
    };

    const filteredObservations = observations.filter(obs =>
        getPatientName(obs.patient_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        obs.code.display?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const stats = {
        total: observations.length,
        vitals: observations.filter(o => o.category === 'vital-signs').length,
        abnormal: observations.filter(o => o.interpretation === 'abnormal' || o.interpretation === 'high' || o.interpretation === 'low').length,
        final: observations.filter(o => o.status === 'final').length
    };

    return (
        <div className="space-y-8 pb-10">
            {/* Flat Header */}
            <div className="flex items-center justify-between sticky top-[4rem] z-20 bg-white dark:bg-gray-900 py-4 -mx-6 px-6 border-b-2 border-gray-100 dark:border-gray-800">
                <div>
                    <h1 className="text-2xl font-heading text-gray-900 dark:text-white">Observations</h1>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Vital signs, lab results, and clinical measurements</p>
                </div>
                <Button
                    onClick={() => setOpen(true)}
                    className="flat-btn-primary"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    Record Vitals
                </Button>
            </div>

            {/* Flat Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Records</span>
                        <FileText className="w-5 h-5 text-blue-500" />
                    </div>
                    <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.total}</div>
                </div>

                <div className="bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-200 dark:border-purple-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Vital Signs</span>
                        <Activity className="w-5 h-5 text-purple-500" />
                    </div>
                    <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">{stats.vitals}</div>
                </div>

                <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Abnormal</span>
                        <AlertCircle className="w-5 h-5 text-red-500" />
                    </div>
                    <div className="text-3xl font-bold text-red-600 dark:text-red-400">{stats.abnormal}</div>
                </div>

                <div className="bg-emerald-50 dark:bg-emerald-900/20 border-2 border-emerald-200 dark:border-emerald-800 rounded-lg p-5 transition-all hover:scale-[1.02]">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Finalized</span>
                        <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    </div>
                    <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{stats.final}</div>
                </div>
            </div>

            {/* List */}
            <Card className="border-border shadow-sm">
                <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <CardTitle>Clinical Observations</CardTitle>
                            <p className="text-sm text-muted-foreground">
                                Recent measurements and test results.
                            </p>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="mb-6 flex flex-col sm:flex-row items-center gap-4">
                        <div className="relative flex-1 w-full">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search by patient or test name..."
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
                                    <TableHead className="font-semibold">Test / Observation</TableHead>
                                    <TableHead className="font-semibold">Value</TableHead>
                                    <TableHead className="font-semibold">Category</TableHead>
                                    <TableHead className="font-semibold">Status</TableHead>
                                    <TableHead className="font-semibold">Date</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    Array.from({ length: 5 }).map((_, i) => (
                                        <TableRow key={i}>
                                            <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[80px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[100px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[80px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[120px]" /></TableCell>
                                        </TableRow>
                                    ))
                                ) : filteredObservations.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                                            No observations found.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredObservations.map((obs) => (
                                        <TableRow key={obs.id} className="group hover:bg-muted/50 transition-colors">
                                            <TableCell className="font-medium">
                                                {getPatientName(obs.patient_id || '')}
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2">
                                                    {obs.category === 'vital-signs' ? (
                                                        <Activity className="h-4 w-4 text-purple-500" />
                                                    ) : (
                                                        <FileText className="h-4 w-4 text-blue-500" />
                                                    )}
                                                    {obs.code.display || obs.code.code}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <span className="font-semibold">
                                                    {obs.value?.value}
                                                </span>
                                                <span className="text-muted-foreground ml-1">
                                                    {obs.value?.unit}
                                                </span>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline" className="capitalize">
                                                    {obs.category}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="secondary" className="capitalize">
                                                    {obs.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground text-sm">
                                                {obs.effective_datetime ? format(new Date(obs.effective_datetime), 'PP p') : '-'}
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>

            {/* Create Dialog */}
            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent className="sm:max-w-[500px] p-0 overflow-hidden rounded-lg border-2 border-gray-200 dark:border-gray-700">
                    <div className="bg-blue-600 px-6 py-5 text-white border-b-2 border-blue-700">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-white/20 rounded-lg border-2 border-white/30">
                                <Activity className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <DialogTitle className="text-lg font-heading text-white">Record Observation</DialogTitle>
                                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                                    Log vital signs or other clinical measurements
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
                                error={!formData.patient_id && submitting} // Optional visual cue
                            />
                        </div>

                        {/* Observation Type (Quick Select) */}
                        <div className="space-y-2">
                            <Label htmlFor="type" className="text-sm font-medium">Observation Type <span className="text-red-500">*</span></Label>
                            <div className="grid grid-cols-2 gap-2">
                                {COMMON_OBSERVATIONS.map((type) => {
                                    const Icon = type.icon;
                                    const isSelected = selectedType === type.code;
                                    return (
                                        <button
                                            key={type.code}
                                            type="button"
                                            onClick={() => setSelectedType(type.code)}
                                            className={`
                                                flex items-center gap-2 p-3 rounded-xl border text-sm font-medium transition-all
                                                ${isSelected
                                                    ? 'border-blue-600 bg-blue-50 text-blue-700 ring-1 ring-blue-600'
                                                    : 'border-border hover:border-blue-200 hover:bg-blue-50/50'
                                                }
                                            `}
                                        >
                                            <Icon className={`w-4 h-4 ${isSelected ? 'text-blue-600' : 'text-muted-foreground'}`} />
                                            {type.label}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Value Input */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="value" className="text-sm font-medium">Value <span className="text-red-500">*</span></Label>
                                <Input
                                    type="number"
                                    step="0.01"
                                    placeholder="0.00"
                                    value={formData.value}
                                    onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                                    className="h-11 rounded-xl"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label className="text-sm font-medium">Unit</Label>
                                <div className="h-11 px-3 flex items-center bg-muted/50 border border-border rounded-xl text-muted-foreground">
                                    {COMMON_OBSERVATIONS.find(t => t.code === selectedType)?.unit || '-'}
                                </div>
                            </div>
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
                                    <SelectItem value="final">Final</SelectItem>
                                    <SelectItem value="preliminary">Preliminary</SelectItem>
                                    <SelectItem value="amended">Amended</SelectItem>
                                    <SelectItem value="registered">Registered</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Note */}
                        <div className="space-y-2">
                            <Label htmlFor="note" className="text-sm font-medium">Notes (Optional)</Label>
                            <Input
                                placeholder="Add any additional comments..."
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
                                {submitting ? 'Saving...' : 'Record Observation'}
                            </Button>
                        </div>
                    </form>
                </DialogContent>
            </Dialog>
        </div>
    );
}
