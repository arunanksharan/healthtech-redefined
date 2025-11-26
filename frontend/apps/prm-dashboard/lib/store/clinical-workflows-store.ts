import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";

// ============================================================================
// Types - Medications & Prescriptions
// ============================================================================

export interface Medication {
  id: string;
  name: string;
  genericName: string;
  brandNames: string[];
  strength: string;
  form: "tablet" | "capsule" | "liquid" | "injection" | "topical" | "inhaler" | "patch" | "drops";
  route: "oral" | "sublingual" | "topical" | "intravenous" | "intramuscular" | "subcutaneous" | "inhaled" | "ophthalmic" | "otic";
  category: string;
  controlledSubstance: boolean;
  scheduleClass?: "II" | "III" | "IV" | "V";
  price?: number;
  priceUnit?: string;
  requiresPriorAuth?: boolean;
}

export interface DrugInteraction {
  id: string;
  drug1: string;
  drug2: string;
  severity: "severe" | "moderate" | "mild";
  description: string;
  recommendation: string;
  evidenceLevel: "A" | "B" | "C" | "D";
  evidenceLink?: string;
}

export interface Prescription {
  id: string;
  patientId: string;
  prescriberId: string;
  medication: Medication;
  dose: number;
  doseUnit: string;
  frequency: string;
  frequencyCode: string;
  route: string;
  duration: number;
  durationUnit: "days" | "weeks" | "months";
  quantity: number;
  quantityUnit: string;
  refills: number;
  dispenseAsWritten: boolean;
  directions: string;
  indication?: string;
  diagnosisCodes?: string[];
  pharmacy?: Pharmacy;
  status: "draft" | "pending" | "signed" | "sent" | "filled" | "cancelled";
  interactions: DrugInteraction[];
  interactionsReviewed: boolean;
  signedAt?: string;
  signedBy?: string;
  sentAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Pharmacy {
  id: string;
  name: string;
  address: string;
  phone: string;
  fax?: string;
  email?: string;
  npi: string;
  isPreferred: boolean;
  supportsElectronic: boolean;
}

// ============================================================================
// Types - Lab Orders
// ============================================================================

export interface LabTest {
  id: string;
  name: string;
  code: string;
  cptCode: string;
  loincCode?: string;
  category: string;
  description: string;
  specimenType: string;
  requiresFasting: boolean;
  fastingHours?: number;
  turnaroundTime: string;
  price?: number;
  commonIndications: string[];
}

export interface LabOrder {
  id: string;
  patientId: string;
  orderingProviderId: string;
  tests: LabTest[];
  priority: "routine" | "urgent" | "stat";
  collectionType: "in-house" | "external" | "patient-collected";
  labFacility?: LabFacility;
  scheduledDate?: string;
  requiresFasting: boolean;
  fastingInstructionsGiven: boolean;
  diagnosis: DiagnosisCode[];
  clinicalNotes?: string;
  status: "draft" | "pending" | "signed" | "collected" | "processing" | "completed" | "cancelled";
  results?: LabResult[];
  signedAt?: string;
  signedBy?: string;
  createdAt: string;
  updatedAt: string;
}

export interface LabFacility {
  id: string;
  name: string;
  address: string;
  phone: string;
  isInNetwork: boolean;
}

export interface LabResult {
  testId: string;
  testName: string;
  value: string;
  unit: string;
  referenceRange: string;
  interpretation: "normal" | "low" | "high" | "critical-low" | "critical-high" | "abnormal";
  resultedAt: string;
  notes?: string;
}

export interface DiagnosisCode {
  code: string;
  description: string;
  type: "ICD-10" | "ICD-9" | "SNOMED";
}

// ============================================================================
// Types - Clinical Documentation
// ============================================================================

export interface ClinicalNote {
  id: string;
  patientId: string;
  encounterId?: string;
  authorId: string;
  noteType: "soap" | "progress" | "procedure" | "consult" | "discharge" | "admission";
  template?: string;
  subjective?: SubjectiveSection;
  objective?: ObjectiveSection;
  assessment?: AssessmentSection;
  plan?: PlanSection;
  freeText?: string;
  status: "draft" | "final" | "amended" | "deleted";
  signedAt?: string;
  signedBy?: string;
  amendedAt?: string;
  amendedBy?: string;
  amendmentReason?: string;
  createdAt: string;
  updatedAt: string;
}

export interface SubjectiveSection {
  chiefComplaint: string;
  historyOfPresentIllness: string;
  reviewOfSystems?: Record<string, string>;
  pastMedicalHistory?: string;
  medications?: string;
  allergies?: string;
  socialHistory?: string;
  familyHistory?: string;
}

export interface ObjectiveSection {
  vitalSigns?: VitalSigns;
  physicalExam?: Record<string, string>;
  labResults?: string;
  imagingResults?: string;
  otherFindings?: string;
}

export interface AssessmentSection {
  diagnoses: AssessmentDiagnosis[];
  clinicalImpression?: string;
}

export interface AssessmentDiagnosis {
  code: string;
  description: string;
  status: "active" | "resolved" | "chronic" | "rule-out";
  notes?: string;
}

export interface PlanSection {
  items: PlanItem[];
  followUp?: string;
  patientEducation?: string;
  ordersPlaced?: string[];
  prescriptionsWritten?: string[];
}

export interface PlanItem {
  category: "medication" | "lab" | "imaging" | "referral" | "procedure" | "lifestyle" | "follow-up" | "other";
  description: string;
  linkedOrderId?: string;
}

// ============================================================================
// Types - Vital Signs
// ============================================================================

export interface VitalSigns {
  id: string;
  patientId: string;
  recordedById: string;
  recordedAt: string;
  bloodPressure?: {
    systolic: number;
    diastolic: number;
    position: "sitting" | "standing" | "supine";
    arm: "left" | "right";
  };
  heartRate?: number;
  respiratoryRate?: number;
  temperature?: {
    value: number;
    unit: "F" | "C";
    location: "oral" | "axillary" | "tympanic" | "rectal" | "temporal";
  };
  oxygenSaturation?: number;
  weight?: {
    value: number;
    unit: "lbs" | "kg";
  };
  height?: {
    value: string;
    unit: "ft-in" | "cm";
  };
  bmi?: number;
  painLevel?: number;
  painLocation?: string;
  bloodGlucose?: {
    value: number;
    timing: "fasting" | "random" | "post-meal";
  };
  notes?: string;
  abnormalFlags: VitalAbnormalFlag[];
}

export interface VitalAbnormalFlag {
  vital: string;
  value: number | string;
  status: "low" | "high" | "critical-low" | "critical-high";
  message: string;
}

export interface VitalThresholds {
  bloodPressure: {
    systolic: { low: number; high: number; criticalLow: number; criticalHigh: number };
    diastolic: { low: number; high: number; criticalLow: number; criticalHigh: number };
  };
  heartRate: { low: number; high: number; criticalLow: number; criticalHigh: number };
  temperature: { low: number; high: number; criticalLow: number; criticalHigh: number };
  oxygenSaturation: { low: number; criticalLow: number };
  respiratoryRate: { low: number; high: number };
}

// ============================================================================
// Types - Referrals
// ============================================================================

export interface Referral {
  id: string;
  patientId: string;
  referringProviderId: string;
  referralType: "consultation" | "transfer" | "co-management";
  specialty: string;
  specialist?: Specialist;
  priority: "routine" | "urgent" | "emergent";
  reasonForReferral: string;
  clinicalHistory?: string;
  attachedDocuments?: AttachedDocument[];
  appointmentDate?: string;
  status: "draft" | "pending" | "sent" | "accepted" | "scheduled" | "completed" | "cancelled" | "declined";
  referralLetter?: string;
  responseNotes?: string;
  signedAt?: string;
  signedBy?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Specialist {
  id: string;
  name: string;
  specialty: string;
  facility: string;
  address: string;
  phone: string;
  fax?: string;
  email?: string;
  npi: string;
  isInNetwork: boolean;
  rating?: number;
  reviewCount?: number;
  nextAvailable?: string;
  estimatedCopay?: number;
}

export interface AttachedDocument {
  id: string;
  name: string;
  type: "lab_result" | "imaging" | "clinical_note" | "medication_list" | "other";
  url: string;
  attachedAt: string;
}

// ============================================================================
// Store State
// ============================================================================

interface ClinicalWorkflowsState {
  // Medications & Prescriptions
  medications: Medication[];
  prescriptions: Prescription[];
  currentPrescription: Partial<Prescription> | null;
  drugInteractions: DrugInteraction[];
  pharmacies: Pharmacy[];

  // Lab Orders
  labTests: LabTest[];
  labOrders: LabOrder[];
  currentLabOrder: Partial<LabOrder> | null;
  labFacilities: LabFacility[];

  // Clinical Notes
  clinicalNotes: ClinicalNote[];
  currentNote: Partial<ClinicalNote> | null;
  noteTemplates: { id: string; name: string; type: string; content: any }[];

  // Vital Signs
  vitalSigns: VitalSigns[];
  currentVitals: Partial<VitalSigns> | null;
  vitalThresholds: VitalThresholds;

  // Referrals
  referrals: Referral[];
  currentReferral: Partial<Referral> | null;
  specialists: Specialist[];

  // Diagnosis Codes
  diagnosisCodes: DiagnosisCode[];

  // UI State
  isLoading: boolean;
  error: string | null;

  // Actions - Prescriptions
  searchMedications: (query: string) => Promise<Medication[]>;
  checkDrugInteractions: (medicationIds: string[], patientId: string) => Promise<DrugInteraction[]>;
  createPrescription: (prescription: Partial<Prescription>) => void;
  updatePrescription: (id: string, updates: Partial<Prescription>) => void;
  signPrescription: (id: string, pin: string) => Promise<void>;
  sendPrescription: (id: string) => Promise<void>;
  cancelPrescription: (id: string, reason: string) => void;

  // Actions - Lab Orders
  searchLabTests: (query: string) => Promise<LabTest[]>;
  createLabOrder: (order: Partial<LabOrder>) => void;
  updateLabOrder: (id: string, updates: Partial<LabOrder>) => void;
  signLabOrder: (id: string) => Promise<void>;
  cancelLabOrder: (id: string, reason: string) => void;

  // Actions - Clinical Notes
  createNote: (note: Partial<ClinicalNote>) => void;
  updateNote: (id: string, updates: Partial<ClinicalNote>) => void;
  generateSOAPFromVoice: (transcript: string) => Promise<Partial<ClinicalNote>>;
  signNote: (id: string) => Promise<void>;
  amendNote: (id: string, amendments: Partial<ClinicalNote>, reason: string) => void;

  // Actions - Vital Signs
  recordVitals: (vitals: Partial<VitalSigns>) => void;
  validateVitals: (vitals: Partial<VitalSigns>) => VitalAbnormalFlag[];

  // Actions - Referrals
  searchSpecialists: (specialty: string, insuranceId?: string) => Promise<Specialist[]>;
  createReferral: (referral: Partial<Referral>) => void;
  updateReferral: (id: string, updates: Partial<Referral>) => void;
  generateReferralLetter: (referralId: string) => Promise<string>;
  sendReferral: (id: string) => Promise<void>;

  // Actions - Diagnosis
  searchDiagnosis: (query: string) => Promise<DiagnosisCode[]>;

  // General Actions
  setError: (error: string | null) => void;
  clearCurrentItems: () => void;
}

// ============================================================================
// Default Thresholds
// ============================================================================

const DEFAULT_VITAL_THRESHOLDS: VitalThresholds = {
  bloodPressure: {
    systolic: { low: 90, high: 140, criticalLow: 80, criticalHigh: 180 },
    diastolic: { low: 60, high: 90, criticalLow: 50, criticalHigh: 120 },
  },
  heartRate: { low: 60, high: 100, criticalLow: 40, criticalHigh: 150 },
  temperature: { low: 97.0, high: 99.5, criticalLow: 95.0, criticalHigh: 104.0 },
  oxygenSaturation: { low: 95, criticalLow: 90 },
  respiratoryRate: { low: 12, high: 20 },
};

// ============================================================================
// Mock Data Generators
// ============================================================================

const createMockMedications = (): Medication[] => [
  {
    id: "med-1",
    name: "Metformin",
    genericName: "Metformin Hydrochloride",
    brandNames: ["Glucophage", "Fortamet"],
    strength: "500mg",
    form: "tablet",
    route: "oral",
    category: "Antidiabetic",
    controlledSubstance: false,
    price: 45,
    priceUnit: "strip of 10",
  },
  {
    id: "med-2",
    name: "Metformin",
    genericName: "Metformin Hydrochloride",
    brandNames: ["Glucophage", "Fortamet"],
    strength: "1000mg",
    form: "tablet",
    route: "oral",
    category: "Antidiabetic",
    controlledSubstance: false,
    price: 85,
    priceUnit: "strip of 10",
  },
  {
    id: "med-3",
    name: "Lisinopril",
    genericName: "Lisinopril",
    brandNames: ["Prinivil", "Zestril"],
    strength: "10mg",
    form: "tablet",
    route: "oral",
    category: "ACE Inhibitor",
    controlledSubstance: false,
    price: 35,
    priceUnit: "strip of 10",
  },
  {
    id: "med-4",
    name: "Atorvastatin",
    genericName: "Atorvastatin Calcium",
    brandNames: ["Lipitor"],
    strength: "20mg",
    form: "tablet",
    route: "oral",
    category: "Statin",
    controlledSubstance: false,
    price: 65,
    priceUnit: "strip of 10",
  },
  {
    id: "med-5",
    name: "Omeprazole",
    genericName: "Omeprazole",
    brandNames: ["Prilosec"],
    strength: "20mg",
    form: "capsule",
    route: "oral",
    category: "Proton Pump Inhibitor",
    controlledSubstance: false,
    price: 55,
    priceUnit: "strip of 14",
  },
];

const createMockLabTests = (): LabTest[] => [
  {
    id: "lab-1",
    name: "Hemoglobin A1C (HbA1c)",
    code: "HBA1C",
    cptCode: "83036",
    loincCode: "4548-4",
    category: "Diabetes",
    description: "Measures average blood sugar over 2-3 months",
    specimenType: "Blood",
    requiresFasting: false,
    turnaroundTime: "1-2 days",
    price: 450,
    commonIndications: ["Diabetes monitoring", "Diabetes screening"],
  },
  {
    id: "lab-2",
    name: "Lipid Panel",
    code: "LIPID",
    cptCode: "80061",
    loincCode: "57698-3",
    category: "Cardiovascular",
    description: "Total Cholesterol, LDL, HDL, Triglycerides",
    specimenType: "Blood",
    requiresFasting: true,
    fastingHours: 12,
    turnaroundTime: "1 day",
    price: 650,
    commonIndications: ["Cardiovascular risk assessment", "Statin therapy monitoring"],
  },
  {
    id: "lab-3",
    name: "Complete Blood Count (CBC)",
    code: "CBC",
    cptCode: "85025",
    loincCode: "58410-2",
    category: "Hematology",
    description: "Red cells, white cells, platelets, hemoglobin",
    specimenType: "Blood",
    requiresFasting: false,
    turnaroundTime: "Same day",
    price: 350,
    commonIndications: ["General health check", "Anemia workup", "Infection workup"],
  },
  {
    id: "lab-4",
    name: "Comprehensive Metabolic Panel",
    code: "CMP",
    cptCode: "80053",
    loincCode: "24323-8",
    category: "Chemistry",
    description: "Glucose, electrolytes, kidney function, liver function",
    specimenType: "Blood",
    requiresFasting: true,
    fastingHours: 8,
    turnaroundTime: "1 day",
    price: 750,
    commonIndications: ["General health check", "Medication monitoring"],
  },
  {
    id: "lab-5",
    name: "Thyroid Stimulating Hormone (TSH)",
    code: "TSH",
    cptCode: "84443",
    loincCode: "3016-3",
    category: "Endocrine",
    description: "Thyroid function screening",
    specimenType: "Blood",
    requiresFasting: false,
    turnaroundTime: "1-2 days",
    price: 400,
    commonIndications: ["Thyroid screening", "Thyroid medication monitoring"],
  },
];

const createMockSpecialists = (): Specialist[] => [
  {
    id: "spec-1",
    name: "Dr. Priya Mehta",
    specialty: "Endocrinology",
    facility: "Surya Hospital, Indiranagar",
    address: "123 Indiranagar, Bangalore",
    phone: "+91-9876543210",
    email: "priya.mehta@surya.com",
    npi: "1234567890",
    isInNetwork: true,
    rating: 4.8,
    reviewCount: 120,
    nextAvailable: "2024-12-02",
    estimatedCopay: 500,
  },
  {
    id: "spec-2",
    name: "Dr. Arun Gupta",
    specialty: "Endocrinology",
    facility: "City Hospital",
    address: "456 MG Road, Bangalore",
    phone: "+91-9876543211",
    email: "arun.gupta@cityhospital.com",
    npi: "1234567891",
    isInNetwork: true,
    rating: 4.6,
    reviewCount: 85,
    nextAvailable: "2024-12-05",
    estimatedCopay: 600,
  },
  {
    id: "spec-3",
    name: "Dr. Sanjay Rao",
    specialty: "Cardiology",
    facility: "Heart Care Center",
    address: "789 HSR Layout, Bangalore",
    phone: "+91-9876543212",
    email: "sanjay.rao@heartcare.com",
    npi: "1234567892",
    isInNetwork: true,
    rating: 4.9,
    reviewCount: 200,
    nextAvailable: "2024-12-03",
    estimatedCopay: 750,
  },
];

const createMockPharmacies = (): Pharmacy[] => [
  {
    id: "pharm-1",
    name: "Apollo Pharmacy, Whitefield",
    address: "123 Whitefield Main Road, Bangalore",
    phone: "+91-80-12345678",
    fax: "+91-80-12345679",
    email: "whitefield@apollopharmacy.com",
    npi: "9876543210",
    isPreferred: true,
    supportsElectronic: true,
  },
  {
    id: "pharm-2",
    name: "MedPlus, Indiranagar",
    address: "456 100ft Road, Indiranagar, Bangalore",
    phone: "+91-80-23456789",
    email: "indiranagar@medplus.com",
    npi: "9876543211",
    isPreferred: false,
    supportsElectronic: true,
  },
];

// ============================================================================
// Store Implementation
// ============================================================================

export const useClinicalWorkflowsStore = create<ClinicalWorkflowsState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial State
      medications: createMockMedications(),
      prescriptions: [],
      currentPrescription: null,
      drugInteractions: [],
      pharmacies: createMockPharmacies(),

      labTests: createMockLabTests(),
      labOrders: [],
      currentLabOrder: null,
      labFacilities: [],

      clinicalNotes: [],
      currentNote: null,
      noteTemplates: [],

      vitalSigns: [],
      currentVitals: null,
      vitalThresholds: DEFAULT_VITAL_THRESHOLDS,

      referrals: [],
      currentReferral: null,
      specialists: createMockSpecialists(),

      diagnosisCodes: [],

      isLoading: false,
      error: null,

      // Prescription Actions
      searchMedications: async (query: string) => {
        const { medications } = get();
        const lowerQuery = query.toLowerCase();
        return medications.filter(
          (m) =>
            m.name.toLowerCase().includes(lowerQuery) ||
            m.genericName.toLowerCase().includes(lowerQuery) ||
            m.brandNames.some((b) => b.toLowerCase().includes(lowerQuery))
        );
      },

      checkDrugInteractions: async (medicationIds: string[], patientId: string) => {
        // Mock interaction check
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Return mock interaction if Metformin and Lisinopril are both selected
        if (medicationIds.some((id) => id.includes("med-1") || id.includes("med-2")) &&
            medicationIds.some((id) => id.includes("med-3"))) {
          return [
            {
              id: "int-1",
              drug1: "Metformin",
              drug2: "Lisinopril",
              severity: "moderate",
              description: "Increased hypoglycemia risk",
              recommendation: "Monitor blood glucose closely. Consider reducing Metformin dose if hypoglycemia occurs.",
              evidenceLevel: "B" as const,
            },
          ];
        }
        return [];
      },

      createPrescription: (prescription) => {
        set({ currentPrescription: prescription });
      },

      updatePrescription: (id, updates) => {
        set((state) => ({
          prescriptions: state.prescriptions.map((p) =>
            p.id === id ? { ...p, ...updates, updatedAt: new Date().toISOString() } : p
          ),
        }));
      },

      signPrescription: async (id: string, pin: string) => {
        // Mock signature verification
        await new Promise((resolve) => setTimeout(resolve, 500));
        set((state) => ({
          prescriptions: state.prescriptions.map((p) =>
            p.id === id
              ? { ...p, status: "signed" as const, signedAt: new Date().toISOString(), signedBy: "current-user" }
              : p
          ),
        }));
      },

      sendPrescription: async (id: string) => {
        await new Promise((resolve) => setTimeout(resolve, 500));
        set((state) => ({
          prescriptions: state.prescriptions.map((p) =>
            p.id === id ? { ...p, status: "sent" as const, sentAt: new Date().toISOString() } : p
          ),
        }));
      },

      cancelPrescription: (id, reason) => {
        set((state) => ({
          prescriptions: state.prescriptions.map((p) =>
            p.id === id ? { ...p, status: "cancelled" as const } : p
          ),
        }));
      },

      // Lab Order Actions
      searchLabTests: async (query: string) => {
        const { labTests } = get();
        const lowerQuery = query.toLowerCase();
        return labTests.filter(
          (t) =>
            t.name.toLowerCase().includes(lowerQuery) ||
            t.code.toLowerCase().includes(lowerQuery) ||
            t.category.toLowerCase().includes(lowerQuery)
        );
      },

      createLabOrder: (order) => {
        set({ currentLabOrder: order });
      },

      updateLabOrder: (id, updates) => {
        set((state) => ({
          labOrders: state.labOrders.map((o) =>
            o.id === id ? { ...o, ...updates, updatedAt: new Date().toISOString() } : o
          ),
        }));
      },

      signLabOrder: async (id: string) => {
        await new Promise((resolve) => setTimeout(resolve, 500));
        set((state) => ({
          labOrders: state.labOrders.map((o) =>
            o.id === id
              ? { ...o, status: "signed" as const, signedAt: new Date().toISOString(), signedBy: "current-user" }
              : o
          ),
        }));
      },

      cancelLabOrder: (id, reason) => {
        set((state) => ({
          labOrders: state.labOrders.map((o) =>
            o.id === id ? { ...o, status: "cancelled" as const } : o
          ),
        }));
      },

      // Clinical Note Actions
      createNote: (note) => {
        set({ currentNote: note });
      },

      updateNote: (id, updates) => {
        set((state) => ({
          clinicalNotes: state.clinicalNotes.map((n) =>
            n.id === id ? { ...n, ...updates, updatedAt: new Date().toISOString() } : n
          ),
        }));
      },

      generateSOAPFromVoice: async (transcript: string) => {
        // Mock AI generation
        await new Promise((resolve) => setTimeout(resolve, 1500));

        return {
          noteType: "soap" as const,
          subjective: {
            chiefComplaint: "Diabetes and hypertension follow-up",
            historyOfPresentIllness: "59-year-old male presents for routine follow-up of Type 2 Diabetes and Hypertension. Patient reports medication compliance but experiencing gastrointestinal upset since Metformin dose increase.",
          },
          objective: {
            physicalExam: {
              general: "Alert, oriented, no acute distress",
              cardiovascular: "Regular rate and rhythm, no murmurs",
            },
          },
          assessment: {
            diagnoses: [
              { code: "E11.9", description: "Type 2 Diabetes Mellitus", status: "active" as const },
              { code: "I10", description: "Essential Hypertension", status: "active" as const },
            ],
          },
          plan: {
            items: [
              { category: "medication" as const, description: "Continue Metformin 1000mg BID with food" },
              { category: "lifestyle" as const, description: "Weight management, low sodium diet" },
              { category: "follow-up" as const, description: "Return in 4 weeks" },
            ],
          },
        };
      },

      signNote: async (id: string) => {
        await new Promise((resolve) => setTimeout(resolve, 500));
        set((state) => ({
          clinicalNotes: state.clinicalNotes.map((n) =>
            n.id === id
              ? { ...n, status: "final" as const, signedAt: new Date().toISOString(), signedBy: "current-user" }
              : n
          ),
        }));
      },

      amendNote: (id, amendments, reason) => {
        set((state) => ({
          clinicalNotes: state.clinicalNotes.map((n) =>
            n.id === id
              ? {
                  ...n,
                  ...amendments,
                  status: "amended" as const,
                  amendedAt: new Date().toISOString(),
                  amendedBy: "current-user",
                  amendmentReason: reason,
                }
              : n
          ),
        }));
      },

      // Vital Signs Actions
      recordVitals: (vitals) => {
        const flags = get().validateVitals(vitals);
        const newVitals: VitalSigns = {
          ...vitals,
          id: `vitals-${Date.now()}`,
          recordedAt: new Date().toISOString(),
          abnormalFlags: flags,
        } as VitalSigns;

        set((state) => ({
          vitalSigns: [newVitals, ...state.vitalSigns],
          currentVitals: null,
        }));
      },

      validateVitals: (vitals) => {
        const { vitalThresholds } = get();
        const flags: VitalAbnormalFlag[] = [];

        // Blood pressure validation
        if (vitals.bloodPressure) {
          const { systolic, diastolic } = vitals.bloodPressure;
          const sysThresh = vitalThresholds.bloodPressure.systolic;
          const diaThresh = vitalThresholds.bloodPressure.diastolic;

          if (systolic >= sysThresh.criticalHigh) {
            flags.push({ vital: "BP Systolic", value: systolic, status: "critical-high", message: "Critical: Hypertensive crisis" });
          } else if (systolic >= sysThresh.high) {
            flags.push({ vital: "BP Systolic", value: systolic, status: "high", message: "Elevated blood pressure" });
          } else if (systolic <= sysThresh.criticalLow) {
            flags.push({ vital: "BP Systolic", value: systolic, status: "critical-low", message: "Critical: Severe hypotension" });
          }

          if (diastolic >= diaThresh.criticalHigh) {
            flags.push({ vital: "BP Diastolic", value: diastolic, status: "critical-high", message: "Critical: Diastolic hypertension" });
          } else if (diastolic >= diaThresh.high) {
            flags.push({ vital: "BP Diastolic", value: diastolic, status: "high", message: "Elevated diastolic pressure" });
          }
        }

        // Heart rate validation
        if (vitals.heartRate) {
          const hrThresh = vitalThresholds.heartRate;
          if (vitals.heartRate >= hrThresh.criticalHigh) {
            flags.push({ vital: "Heart Rate", value: vitals.heartRate, status: "critical-high", message: "Critical: Severe tachycardia" });
          } else if (vitals.heartRate >= hrThresh.high) {
            flags.push({ vital: "Heart Rate", value: vitals.heartRate, status: "high", message: "Tachycardia" });
          } else if (vitals.heartRate <= hrThresh.criticalLow) {
            flags.push({ vital: "Heart Rate", value: vitals.heartRate, status: "critical-low", message: "Critical: Severe bradycardia" });
          } else if (vitals.heartRate <= hrThresh.low) {
            flags.push({ vital: "Heart Rate", value: vitals.heartRate, status: "low", message: "Bradycardia" });
          }
        }

        // Oxygen saturation validation
        if (vitals.oxygenSaturation) {
          const o2Thresh = vitalThresholds.oxygenSaturation;
          if (vitals.oxygenSaturation <= o2Thresh.criticalLow) {
            flags.push({ vital: "SpO2", value: vitals.oxygenSaturation, status: "critical-low", message: "Critical: Severe hypoxemia" });
          } else if (vitals.oxygenSaturation <= o2Thresh.low) {
            flags.push({ vital: "SpO2", value: vitals.oxygenSaturation, status: "low", message: "Low oxygen saturation" });
          }
        }

        return flags;
      },

      // Referral Actions
      searchSpecialists: async (specialty: string, insuranceId?: string) => {
        const { specialists } = get();
        return specialists.filter(
          (s) =>
            s.specialty.toLowerCase() === specialty.toLowerCase() &&
            (!insuranceId || s.isInNetwork)
        );
      },

      createReferral: (referral) => {
        set({ currentReferral: referral });
      },

      updateReferral: (id, updates) => {
        set((state) => ({
          referrals: state.referrals.map((r) =>
            r.id === id ? { ...r, ...updates, updatedAt: new Date().toISOString() } : r
          ),
        }));
      },

      generateReferralLetter: async (referralId: string) => {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return `Dear Dr. [Specialist Name],

I am referring [Patient Name] to your care for consultation regarding diabetes management.

Clinical Summary:
Patient is a 59-year-old male with Type 2 Diabetes Mellitus with A1C above target despite Metformin therapy. Currently experiencing GI side effects with Metformin 1000mg BID.

Request:
Please evaluate for alternative medication options including consideration of SGLT2 inhibitors or GLP-1 agonists.

Thank you for your assistance with this patient's care.

Sincerely,
Dr. [Referring Physician]`;
      },

      sendReferral: async (id: string) => {
        await new Promise((resolve) => setTimeout(resolve, 500));
        set((state) => ({
          referrals: state.referrals.map((r) =>
            r.id === id
              ? { ...r, status: "sent" as const, signedAt: new Date().toISOString(), signedBy: "current-user" }
              : r
          ),
        }));
      },

      // Diagnosis Search
      searchDiagnosis: async (query: string) => {
        // Mock diagnosis search
        await new Promise((resolve) => setTimeout(resolve, 300));
        const mockCodes: DiagnosisCode[] = [
          { code: "E11.9", description: "Type 2 Diabetes Mellitus without complications", type: "ICD-10" },
          { code: "E11.65", description: "Type 2 Diabetes Mellitus with hyperglycemia", type: "ICD-10" },
          { code: "I10", description: "Essential (primary) hypertension", type: "ICD-10" },
          { code: "E78.5", description: "Hyperlipidemia, unspecified", type: "ICD-10" },
          { code: "Z79.84", description: "Long term (current) use of oral hypoglycemic drugs", type: "ICD-10" },
        ];

        const lowerQuery = query.toLowerCase();
        return mockCodes.filter(
          (c) =>
            c.code.toLowerCase().includes(lowerQuery) ||
            c.description.toLowerCase().includes(lowerQuery)
        );
      },

      // General Actions
      setError: (error) => set({ error }),

      clearCurrentItems: () =>
        set({
          currentPrescription: null,
          currentLabOrder: null,
          currentNote: null,
          currentVitals: null,
          currentReferral: null,
        }),
    })),
    { name: "clinical-workflows-store" }
  )
);

export default useClinicalWorkflowsStore;
