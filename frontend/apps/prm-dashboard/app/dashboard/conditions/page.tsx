'use client';

import { useEffect, useState } from 'react';
import {
    Plus,
    Search,
    Stethoscope,
    Activity,
    AlertTriangle,
    CheckCircle2,
    Calendar,
    Thermometer,
    Heart
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
    getConditions,
    createCondition,
    CreateConditionData
} from '@/lib/api/conditions';
import { patientsAPI } from '@/lib/api/patients';
import { Condition } from '@/lib/api/types';
import { Patient } from '@/lib/types';
import { PatientCombobox } from '@/components/dashboard/patient-combobox';

// Common Conditions Helpers
const COMMON_CONDITIONS = [
    { label: 'Essential Hypertension', code: 'I10', system: 'http://hl7.org/fhir/sid/icd-10' },
    { label: 'Type 2 Diabetes Mellitus', code: 'E11', system: 'http://hl7.org/fhir/sid/icd-10' },
    { label: 'Asthma', code: 'J45', system: 'http://hl7.org/fhir/sid/icd-10' },
    { label: 'COVID-19', code: 'U07.1', system: 'http://hl7.org/fhir/sid/icd-10' },
    { label: 'Acute Bronchitis', code: 'J20', system: 'http://hl7.org/fhir/sid/icd-10' },
    { label: 'Gastroesophageal Reflux Disease', code: 'K21.9', system: 'http://hl7.org/fhir/sid/icd-10' },
];

export default function ConditionsPage() {
    const [loading, setLoading] = useState(true);
    const [conditions, setConditions] = useState<Condition[]>([]);
    const [patients, setPatients] = useState<Patient[]>([]);
    const [searchQuery, setSearchQuery] = useState('');

    // Dialog State
    const [open, setOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Form State
    const [selectedCommon, setSelectedCommon] = useState<string>(''); // code
    const [formData, setFormData] = useState({
        patient_id: '',
        clinical_status: 'active',
        verification_status: 'confirmed',
        category: 'problem-list-item',
        severity: 'moderate',
        code_system: 'http://hl7.org/fhir/sid/icd-10',
        code_code: '',
        code_display: '',
        onset_datetime: '',
        note: ''
    });

    const fetchData = async () => {
        setLoading(true);
        try {
            const [condRes, patRes] = await Promise.all([
                getConditions({ page: 1, page_size: 100 }),
                patientsAPI.getAll({ page_size: 100 })
            ]);

            const [condData, condError] = condRes;
            const [patData, patError] = patRes;

            if (condError) {
                console.error('Failed to fetch conditions:', condError);
                toast.error('Failed to load conditions');
            } else if (condData) {
                setConditions(condData.items);
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

    // Handle common condition selection
    useEffect(() => {
        if (selectedCommon) {
            const found = COMMON_CONDITIONS.find(c => c.code === selectedCommon);
            if (found) {
                setFormData(prev => ({
                    ...prev,
                    code_code: found.code,
                    code_display: found.label,
                    code_system: found.system
                }));
            }
        }
    }, [selectedCommon]);

    // Reset form
    useEffect(() => {
        if (!open) {
            setSelectedCommon('');
            setFormData({
                patient_id: '',
                clinical_status: 'active',
                verification_status: 'confirmed',
                category: 'problem-list-item',
                severity: 'moderate',
                code_system: 'http://hl7.org/fhir/sid/icd-10',
                code_code: '',
                code_display: '',
                onset_datetime: '',
                note: ''
            });
        }
    }, [open]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.patient_id || !formData.code_code || !formData.code_display) {
            toast.error('Please fill in required fields');
            return;
        }

        setSubmitting(true);

        const payload: CreateConditionData = {
            tenant_id: '00000000-0000-0000-0000-000000000001',
            patient_id: formData.patient_id,
            clinical_status: formData.clinical_status,
            verification_status: formData.verification_status,
            category: formData.category,
            severity: formData.severity,
            code: {
                system: formData.code_system,
                code: formData.code_code,
                display: formData.code_display
            },
            note: formData.note,
            onset_datetime: formData.onset_datetime || undefined
        };

        const [result, error] = await createCondition(payload);

        if (error) {
            console.error('Failed to create condition:', error);
            toast.error(error.message || 'Failed to create condition');
        } else if (result) {
            toast.success('Condition recorded successfully');
            setOpen(false);
            fetchData();
        }
        setSubmitting(false);
    };

    const getPatientName = (id: string) => {
        const p = patients.find(p => p.id === id);
        return p ? `${p.first_name} ${p.last_name}` : 'Unknown Patient';
    };

    const filteredConditions = conditions.filter(c =>
        getPatientName(c.patient_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.code.display?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const stats = {
        total: conditions.length,
        active: conditions.filter(c => c.clinical_status === 'active' || c.clinical_status === 'recurrence' || c.clinical_status === 'relapse').length,
        resolved: conditions.filter(c => c.clinical_status === 'resolved' || c.clinical_status === 'remission').length,
        severe: conditions.filter(c => c.severity === 'severe').length
    };

    return (
        <div className="space-y-8 pb-10">
            {/* Header */}
            <div className="flex items-center justify-between sticky top-[4rem] z-20 bg-background/90 backdrop-blur-md py-4 -mx-6 px-6 border-b border-border/50">
                <div>
                    <h1 className="text-2xl font-bold text-foreground tracking-tight">Conditions</h1>
                    <p className="text-muted-foreground text-sm">Patient diagnoses, problems, and health concerns</p>
                </div>
                <Button
                    onClick={() => setOpen(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all rounded-full px-6"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    Record Condition
                </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--primary) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Total Records</CardTitle>
                        <Stethoscope className="w-4 h-4 text-primary" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.total}</div>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--warning) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Active Conditions</CardTitle>
                        <Activity className="w-4 h-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.active}</div>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--destructive) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Severe Cases</CardTitle>
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.severe}</div>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--success) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Resolved</CardTitle>
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.resolved}</div>
                    </CardContent>
                </MagicCard>
            </div>

            {/* List */}
            <Card className="border-border shadow-sm">
                <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <CardTitle>Diagnosis & Problem List</CardTitle>
                            <p className="text-sm text-muted-foreground">
                                Active and historical health conditions.
                            </p>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="mb-6 flex flex-col sm:flex-row items-center gap-4">
                        <div className="relative flex-1 w-full">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search by patient or diagnosis..."
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
                                    <TableHead className="font-semibold">Condition</TableHead>
                                    <TableHead className="font-semibold">Clinical Status</TableHead>
                                    <TableHead className="font-semibold">Severity</TableHead>
                                    <TableHead className="font-semibold">Verification</TableHead>
                                    <TableHead className="font-semibold">Onset Date</TableHead>
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
                                ) : filteredConditions.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                                            No conditions found.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredConditions.map((cond) => (
                                        <TableRow key={cond.id} className="group hover:bg-muted/50 transition-colors">
                                            <TableCell className="font-medium">
                                                {getPatientName(cond.patient_id || '')}
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2 font-medium">
                                                    {cond.code.display || cond.code.code}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant="secondary"
                                                    className={
                                                        cond.clinical_status === 'active' ? 'bg-orange-100 text-orange-700' :
                                                            cond.clinical_status === 'resolved' ? 'bg-green-100 text-green-700' :
                                                                'bg-gray-100 text-gray-700'
                                                    }
                                                >
                                                    {cond.clinical_status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                {cond.severity ? (
                                                    <Badge variant="outline" className={
                                                        cond.severity === 'severe' ? 'border-red-200 bg-red-50 text-red-700' :
                                                            cond.severity === 'moderate' ? 'border-yellow-200 bg-yellow-50 text-yellow-700' : ''
                                                    }>
                                                        {cond.severity}
                                                    </Badge>
                                                ) : '-'}
                                            </TableCell>
                                            <TableCell>
                                                <span className="text-sm text-muted-foreground capitalize">
                                                    {cond.verification_status}
                                                </span>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground text-sm">
                                                {cond.onset_datetime ? format(new Date(cond.onset_datetime), 'PP') : '-'}
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
                <DialogContent className="sm:max-w-[600px] p-0 overflow-hidden rounded-2xl border-border">
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5 text-white">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-white/20 rounded-xl">
                                <Stethoscope className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <DialogTitle className="text-lg font-semibold text-white">Record Condition</DialogTitle>
                                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                                    Add a diagnosis or health concern
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

                        {/* Condition Name */}
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Common Conditions (Quick Select)</Label>
                            <div className="flex flex-wrap gap-2">
                                {COMMON_CONDITIONS.map((c) => (
                                    <Badge
                                        key={c.code}
                                        variant="outline"
                                        className={`cursor-pointer px-3 py-1.5 transition-colors ${selectedCommon === c.code ? 'bg-blue-50 border-blue-500 text-blue-700' : 'hover:bg-muted'}`}
                                        onClick={() => setSelectedCommon(c.code)}
                                    >
                                        {c.label}
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2 col-span-2">
                                <Label htmlFor="code_display" className="text-sm font-medium">Condition Name <span className="text-red-500">*</span></Label>
                                <Input
                                    placeholder="e.g. Hypertension"
                                    value={formData.code_display}
                                    onChange={(e) => setFormData({ ...formData, code_display: e.target.value, code_code: selectedCommon ? formData.code_code : e.target.value.toUpperCase().replace(/\s+/g, '-') })}
                                    className="h-11 rounded-xl"
                                />
                            </div>
                        </div>

                        {/* Statuses */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="clinical_status" className="text-sm font-medium">Clinical Status</Label>
                                <Select
                                    value={formData.clinical_status}
                                    onValueChange={(value) => setFormData({ ...formData, clinical_status: value })}
                                >
                                    <SelectTrigger className="h-11 rounded-xl">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="active">Active</SelectItem>
                                        <SelectItem value="recurrence">Recurrence</SelectItem>
                                        <SelectItem value="relapse">Relapse</SelectItem>
                                        <SelectItem value="inactive">Inactive</SelectItem>
                                        <SelectItem value="remission">Remission</SelectItem>
                                        <SelectItem value="resolved">Resolved</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="severity" className="text-sm font-medium">Severity</Label>
                                <Select
                                    value={formData.severity}
                                    onValueChange={(value) => setFormData({ ...formData, severity: value })}
                                >
                                    <SelectTrigger className="h-11 rounded-xl">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="mild">Mild</SelectItem>
                                        <SelectItem value="moderate">Moderate</SelectItem>
                                        <SelectItem value="severe">Severe</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="onset" className="text-sm font-medium">Onset Date</Label>
                                <Input
                                    type="date"
                                    value={formData.onset_datetime}
                                    onChange={(e) => setFormData({ ...formData, onset_datetime: e.target.value })}
                                    className="h-11 rounded-xl"
                                />
                            </div>
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
                                {submitting ? 'Saving...' : 'Save Condition'}
                            </Button>
                        </div>
                    </form>
                </DialogContent>
            </Dialog>
        </div>
    );
}
