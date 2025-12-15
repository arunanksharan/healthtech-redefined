'use client';

import { useEffect, useState } from 'react';
import {
    Plus,
    Search,
    FileText,
    User,
    Calendar,
    CheckCircle2,
    Activity,
    Video,
    FlaskConical,
    FileBarChart
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { format } from 'date-fns';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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

import { getDiagnosticReports, createDiagnosticReport } from '@/lib/api/diagnostic-reports';
import { patientsAPI } from '@/lib/api/patients';
import { DiagnosticReport } from '@/lib/api/types';
import { Patient } from '@/lib/types';
import { PatientCombobox } from '@/components/dashboard/patient-combobox';

// Common Reports
const COMMON_LABS = [
    { code: 'cbc', label: 'Complete Blood Count', system: 'LOINC' },
    { code: 'cmp', label: 'Comp. Metabolic Panel', system: 'LOINC' },
    { code: 'lipid', label: 'Lipid Panel', system: 'LOINC' },
    { code: 'a1c', label: 'Hemoglobin A1c', system: 'LOINC' },
];

const COMMON_RADS = [
    { code: 'cxr', label: 'Chest X-Ray', system: 'LOINC' },
    { code: 'ct-head', label: 'CT Head', system: 'LOINC' },
    { code: 'mri-brain', label: 'MRI Brain', system: 'LOINC' },
];

export default function DiagnosticReportsPage() {
    const [loading, setLoading] = useState(true);
    const [reports, setReports] = useState<DiagnosticReport[]>([]);
    const [patients, setPatients] = useState<Patient[]>([]);
    const [searchQuery, setSearchQuery] = useState('');

    // Dialog State
    const [open, setOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    const [formData, setFormData] = useState({
        patient_id: '',
        status: 'final',
        category: 'LAB', // LAB or RAD
        code_code: '',
        code_display: '',
        conclusion: '',
        note: ''
    });

    const [selectedCommon, setSelectedCommon] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [repRes, patRes] = await Promise.all([
                getDiagnosticReports({ page: 1, page_size: 100 }),
                patientsAPI.getAll({ page_size: 100 })
            ]);

            const [repData, repError] = repRes;
            const [patData, patError] = patRes;

            if (repError) {
                console.error('Failed to fetch reports:', repError);
                toast.error('Failed to load reports');
            } else if (repData) {
                setReports(repData.items);
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

    // Reset form
    useEffect(() => {
        if (!open) {
            setFormData({
                patient_id: '',
                status: 'final',
                category: 'LAB',
                code_code: '',
                code_display: '',
                conclusion: '',
                note: ''
            });
            setSelectedCommon(null);
        }
    }, [open]);

    // Handle Quick Select
    useEffect(() => {
        if (selectedCommon) {
            const list = formData.category === 'LAB' ? COMMON_LABS : COMMON_RADS;
            const item = list.find(m => m.code === selectedCommon);
            if (item) {
                setFormData(prev => ({
                    ...prev,
                    code_code: item.code,
                    code_display: item.label
                }));
            }
        }
    }, [selectedCommon, formData.category]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.patient_id || !formData.code_display) {
            toast.error('Patient and Report Name are required');
            return;
        }

        setSubmitting(true);

        const payload: Partial<DiagnosticReport> = {
            patient_id: formData.patient_id,
            status: formData.status,
            category: formData.category,
            tenant_id: '00000000-0000-0000-0000-000000000001',
            code: {
                system: 'http://loinc.org',
                code: formData.code_code || formData.code_display.toLowerCase().replace(/\s+/g, '-'),
                display: formData.code_display
            },
            conclusion: formData.conclusion || undefined,
            note: formData.note || undefined,
            issued: new Date().toISOString()
        };

        const [result, error] = await createDiagnosticReport(payload);

        if (error) {
            console.error(`Failed to create report:`, error);
            toast.error(error.message || `Failed to create report`);
        } else if (result) {
            toast.success(`Report created successfully`);
            setOpen(false);
            fetchData();
        }
        setSubmitting(false);
    };

    const getPatientName = (id: string) => {
        const p = patients.find(p => p.id === id);
        return p ? `${p.first_name} ${p.last_name}` : 'Unknown Patient';
    };

    const filteredReports = reports.filter(r =>
        getPatientName(r.patient_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.code.display?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const stats = {
        total: reports.length,
        lab: reports.filter(r => r.category === 'LAB').length,
        rad: reports.filter(r => r.category === 'RAD' || r.category === 'Radiology').length,
    };

    return (
        <div className="space-y-8 pb-10">
            {/* Header */}
            <div className="flex items-center justify-between sticky top-[4rem] z-20 bg-background/90 backdrop-blur-md py-4 -mx-6 px-6 border-b border-border/50">
                <div>
                    <h1 className="text-2xl font-bold text-foreground tracking-tight">Diagnostic Reports</h1>
                    <p className="text-muted-foreground text-sm">Lab results, imaging, and other findings</p>
                </div>
                <Button
                    onClick={() => setOpen(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all rounded-full px-6"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    New Report
                </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--primary) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Total Reports</CardTitle>
                        <FileBarChart className="w-4 h-4 text-primary" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.total}</div>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--info) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Labs</CardTitle>
                        <FlaskConical className="w-4 h-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.lab}</div>
                    </CardContent>
                </MagicCard>

                <MagicCard className="bg-card border border-border shadow-sm" gradientColor="hsl(var(--purple) / 0.2)">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Radiology</CardTitle>
                        <Video className="w-4 h-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{stats.rad}</div>
                    </CardContent>
                </MagicCard>
            </div>

            {/* List */}
            <Card className="border-border shadow-sm">
                <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <CardTitle>Reports List</CardTitle>
                            <p className="text-sm text-muted-foreground">
                                Detailed log of diagnostic findings.
                            </p>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="mb-6 flex flex-col sm:flex-row items-center gap-4">
                        <div className="relative flex-1 w-full">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search by patient or report name..."
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
                                    <TableHead className="font-semibold">Category</TableHead>
                                    <TableHead className="font-semibold">Test Name</TableHead>
                                    <TableHead className="font-semibold">Status</TableHead>
                                    <TableHead className="font-semibold">Date</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    Array.from({ length: 5 }).map((_, i) => (
                                        <TableRow key={i}>
                                            <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[100px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[80px]" /></TableCell>
                                            <TableCell><Skeleton className="h-4 w-[100px]" /></TableCell>
                                        </TableRow>
                                    ))
                                ) : filteredReports.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-32 text-center text-muted-foreground">
                                            No reports found.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredReports.map((rep) => (
                                        <TableRow key={rep.id} className="group hover:bg-muted/50 transition-colors">
                                            <TableCell className="font-medium">
                                                <div className="flex items-center gap-2">
                                                    <div className="p-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                                                        <User className="h-4 w-4" />
                                                    </div>
                                                    {getPatientName(rep.patient_id || '')}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                {rep.category === 'LAB' ? (
                                                    <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700">Laboratory</Badge>
                                                ) : (
                                                    <Badge variant="outline" className="border-purple-200 bg-purple-50 text-purple-700">Radiology</Badge>
                                                )}
                                            </TableCell>
                                            <TableCell>
                                                <div className="font-medium">{rep.code.display}</div>
                                                <div className="text-xs text-muted-foreground">{rep.code.code}</div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant="secondary"
                                                    className={
                                                        rep.status === 'final' ? 'bg-green-100 text-green-700' :
                                                            rep.status === 'preliminary' ? 'bg-yellow-100 text-yellow-700' :
                                                                'bg-gray-100 text-gray-700'
                                                    }
                                                >
                                                    {rep.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground text-sm">
                                                {rep.issued ? format(new Date(rep.issued), 'PP') : '-'}
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
                                <FileText className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <DialogTitle className="text-lg font-semibold text-white">Create Diagnostic Report</DialogTitle>
                                <DialogDescription className="text-blue-100 text-sm mt-0.5">
                                    Record lab results or imaging findings
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

                        {/* Category & Quick Select */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label className="text-sm font-medium">Category</Label>
                                <Select
                                    value={formData.category}
                                    onValueChange={(value) => {
                                        setFormData(prev => ({ ...prev, category: value }));
                                        setSelectedCommon(null); // Reset quick select on category change
                                    }}
                                >
                                    <SelectTrigger className="h-11 rounded-xl">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="LAB">Laboratory</SelectItem>
                                        <SelectItem value="RAD">Radiology</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label className="text-sm font-medium">Common Tests</Label>
                                <div className="flex flex-wrap gap-2">
                                    {(formData.category === 'LAB' ? COMMON_LABS : COMMON_RADS).map((m) => (
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
                        </div>

                        {/* Test Details */}
                        <div className="space-y-2">
                            <Label htmlFor="code" className="text-sm font-medium">Test/Report Name <span className="text-red-500">*</span></Label>
                            <Input
                                placeholder={formData.category === 'LAB' ? "e.g. Complete Blood Count" : "e.g. Chest X-Ray PA/Lat"}
                                value={formData.code_display}
                                onChange={(e) => setFormData({ ...formData, code_display: e.target.value })}
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
                                    <SelectItem value="registered">Registered</SelectItem>
                                    <SelectItem value="preliminary">Preliminary</SelectItem>
                                    <SelectItem value="final">Final</SelectItem>
                                    <SelectItem value="amended">Amended</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Conclusion */}
                        <div className="space-y-2">
                            <Label htmlFor="conclusion" className="text-sm font-medium">Conclusion/Findings</Label>
                            <Textarea
                                placeholder="Summary of the results..."
                                value={formData.conclusion}
                                onChange={(e) => setFormData({ ...formData, conclusion: e.target.value })}
                                className="min-h-[100px] rounded-xl"
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
                                {submitting ? 'Creating...' : 'Create Report'}
                            </Button>
                        </div>
                    </form>
                </DialogContent>
            </Dialog>
        </div>
    );
}
