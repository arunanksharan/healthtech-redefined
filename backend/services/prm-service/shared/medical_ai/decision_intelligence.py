"""
Clinical Decision Intelligence Service

EPIC-010: Medical AI Capabilities
US-010.4: Clinical Decision Intelligence

Evidence-based clinical decision support:
- Treatment recommendations based on guidelines
- Drug interaction checking
- Diagnostic suggestions
- Lab test recommendations
- Referral suggestions
- Evidence citations
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
from uuid import uuid4, UUID


class RecommendationType(str, Enum):
    """Types of clinical recommendations."""
    TREATMENT = "treatment"
    MEDICATION = "medication"
    DIAGNOSTIC_TEST = "diagnostic_test"
    REFERRAL = "referral"
    MONITORING = "monitoring"
    LIFESTYLE = "lifestyle"
    PREVENTION = "prevention"
    FOLLOW_UP = "follow_up"


class EvidenceLevel(str, Enum):
    """Evidence level for recommendations."""
    LEVEL_A = "A"  # Strong: Multiple RCTs or meta-analyses
    LEVEL_B = "B"  # Moderate: Limited RCTs or high-quality observational
    LEVEL_C = "C"  # Weak: Observational studies
    LEVEL_D = "D"  # Expert opinion
    LEVEL_E = "E"  # Expert consensus / Best practice


class RecommendationStrength(str, Enum):
    """Recommendation strength."""
    STRONG_FOR = "strong_for"
    MODERATE_FOR = "moderate_for"
    WEAK_FOR = "weak_for"
    NEUTRAL = "neutral"
    WEAK_AGAINST = "weak_against"
    STRONG_AGAINST = "strong_against"


class InteractionSeverity(str, Enum):
    """Drug interaction severity levels."""
    CONTRAINDICATED = "contraindicated"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"


class AlertCategory(str, Enum):
    """Clinical alert categories."""
    DRUG_INTERACTION = "drug_interaction"
    ALLERGY_CROSS_REACTIVITY = "allergy_cross_reactivity"
    DUPLICATE_THERAPY = "duplicate_therapy"
    DOSE_CHECK = "dose_check"
    AGE_CONTRAINDICATION = "age_contraindication"
    CONDITION_CONTRAINDICATION = "condition_contraindication"
    LAB_MONITORING = "lab_monitoring"
    PREGNANCY_LACTATION = "pregnancy_lactation"


@dataclass
class ClinicalEvidence:
    """Evidence supporting a recommendation."""
    source: str
    guideline_name: str
    publication_year: int
    evidence_level: EvidenceLevel
    citation: str
    url: Optional[str] = None


@dataclass
class DrugInteraction:
    """Drug-drug interaction information."""
    interaction_id: UUID
    drug_a: str
    drug_a_rxnorm: str
    drug_b: str
    drug_b_rxnorm: str
    severity: InteractionSeverity
    description: str
    mechanism: str
    clinical_effect: str
    management: str
    evidence: List[ClinicalEvidence] = field(default_factory=list)


@dataclass
class ClinicalRecommendation:
    """Clinical recommendation with evidence."""
    recommendation_id: UUID
    recommendation_type: RecommendationType
    title: str
    description: str
    rationale: str
    strength: RecommendationStrength
    evidence_level: EvidenceLevel

    # Actions
    suggested_actions: List[str]
    alternatives: List[str]

    # Context
    applicable_conditions: List[str]
    contraindications: List[str]

    # Evidence
    evidence_citations: List[ClinicalEvidence]

    # Personalization
    patient_specific_notes: List[str] = field(default_factory=list)

    # Confidence
    confidence_score: float = 0.8

    # Metadata
    guideline_source: Optional[str] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DiagnosticSuggestion:
    """Differential diagnosis suggestion."""
    suggestion_id: UUID
    condition_name: str
    icd10_code: str
    snomed_code: str
    probability: float  # 0.0 to 1.0
    supporting_findings: List[str]
    against_findings: List[str]
    recommended_tests: List[str]
    red_flags: List[str]
    typical_presentation: str


@dataclass
class ClinicalAlert:
    """Clinical decision support alert."""
    alert_id: UUID
    category: AlertCategory
    severity: str  # info, warning, critical
    title: str
    message: str
    rationale: str
    suggested_action: str
    override_reason_required: bool = False
    evidence: Optional[ClinicalEvidence] = None


@dataclass
class DecisionSupportResult:
    """Complete decision support result."""
    result_id: UUID
    patient_context: Dict[str, Any]

    # Recommendations
    treatment_recommendations: List[ClinicalRecommendation]
    diagnostic_suggestions: List[DiagnosticSuggestion]
    referral_suggestions: List[ClinicalRecommendation]
    monitoring_recommendations: List[ClinicalRecommendation]

    # Alerts
    alerts: List[ClinicalAlert]
    drug_interactions: List[DrugInteraction]

    # Summary
    summary: str
    priority_actions: List[str]

    # Metadata
    processing_time_ms: float
    created_at: datetime


class ClinicalGuidelineEngine:
    """Engine for clinical guideline-based recommendations."""

    def __init__(self):
        self.guidelines = self._load_clinical_guidelines()

    def _load_clinical_guidelines(self) -> Dict[str, Dict]:
        """Load clinical practice guidelines."""
        return {
            # Hypertension
            'hypertension': {
                'name': 'Hypertension Management',
                'source': 'ACC/AHA 2017 Guidelines',
                'recommendations': [
                    {
                        'condition': 'BP >= 130/80',
                        'type': RecommendationType.TREATMENT,
                        'title': 'Blood Pressure Treatment Goal',
                        'description': 'Target BP < 130/80 mmHg for most adults with hypertension',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_A,
                        'actions': [
                            'Initiate lifestyle modifications',
                            'Consider pharmacotherapy based on cardiovascular risk'
                        ]
                    },
                    {
                        'condition': 'Stage 1 HTN + low CVD risk',
                        'type': RecommendationType.LIFESTYLE,
                        'title': 'Lifestyle Modifications',
                        'description': 'Weight loss, DASH diet, sodium restriction, physical activity',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_A,
                        'actions': [
                            'DASH diet or similar heart-healthy diet',
                            'Reduce sodium to < 1500 mg/day',
                            '150 minutes/week of moderate aerobic exercise',
                            'Weight loss if overweight/obese',
                            'Limit alcohol consumption'
                        ]
                    },
                    {
                        'condition': 'HTN + diabetes',
                        'type': RecommendationType.MEDICATION,
                        'title': 'First-line Antihypertensive for Diabetic Patients',
                        'description': 'ACE inhibitor or ARB preferred for patients with diabetes',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_A,
                        'actions': [
                            'Start ACE inhibitor (e.g., lisinopril) or ARB',
                            'Monitor potassium and creatinine',
                            'Avoid ACE inhibitor + ARB combination'
                        ]
                    }
                ]
            },

            # Diabetes
            'diabetes_type2': {
                'name': 'Type 2 Diabetes Management',
                'source': 'ADA Standards of Care 2024',
                'recommendations': [
                    {
                        'condition': 'newly diagnosed T2DM',
                        'type': RecommendationType.MEDICATION,
                        'title': 'First-line Therapy',
                        'description': 'Metformin as initial pharmacologic therapy',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_A,
                        'actions': [
                            'Start metformin unless contraindicated',
                            'Begin with 500mg daily, titrate to 2000mg/day',
                            'Monitor renal function',
                            'Add lifestyle modifications'
                        ]
                    },
                    {
                        'condition': 'T2DM + ASCVD',
                        'type': RecommendationType.MEDICATION,
                        'title': 'Add GLP-1 RA or SGLT2i',
                        'description': 'Add GLP-1 receptor agonist or SGLT2 inhibitor for cardiovascular benefit',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_A,
                        'actions': [
                            'Add semaglutide, liraglutide, or dulaglutide',
                            'Or add empagliflozin or dapagliflozin',
                            'Continue metformin',
                            'Monitor HbA1c quarterly until stable'
                        ]
                    },
                    {
                        'condition': 'T2DM + CKD',
                        'type': RecommendationType.MEDICATION,
                        'title': 'SGLT2 Inhibitor for Kidney Protection',
                        'description': 'SGLT2 inhibitor provides renal protection in diabetic kidney disease',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_A,
                        'actions': [
                            'Add empagliflozin or dapagliflozin',
                            'Monitor eGFR and adjust metformin dose if needed',
                            'Check for euglycemic DKA symptoms'
                        ]
                    },
                    {
                        'condition': 'HbA1c monitoring',
                        'type': RecommendationType.MONITORING,
                        'title': 'HbA1c Testing Frequency',
                        'description': 'Monitor HbA1c at least twice yearly if stable, quarterly if adjusting therapy',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_B,
                        'actions': [
                            'Check HbA1c every 3 months if not at goal',
                            'Check HbA1c every 6 months if stable at goal',
                            'Target HbA1c < 7% for most adults'
                        ]
                    }
                ]
            },

            # Heart Failure
            'heart_failure': {
                'name': 'Heart Failure Management',
                'source': 'ACC/AHA/HFSA 2022 Guidelines',
                'recommendations': [
                    {
                        'condition': 'HFrEF (EF <= 40%)',
                        'type': RecommendationType.MEDICATION,
                        'title': 'Guideline-Directed Medical Therapy',
                        'description': 'Four pillars of HFrEF therapy: ACEi/ARNI, BB, MRA, SGLT2i',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_A,
                        'actions': [
                            'Start ACE inhibitor or ARNI (sacubitril/valsartan)',
                            'Add beta-blocker (carvedilol, metoprolol succinate, or bisoprolol)',
                            'Add mineralocorticoid receptor antagonist (spironolactone or eplerenone)',
                            'Add SGLT2 inhibitor (dapagliflozin or empagliflozin)',
                            'Titrate medications to target doses'
                        ]
                    },
                    {
                        'condition': 'HF + congestion',
                        'type': RecommendationType.MEDICATION,
                        'title': 'Diuretic Therapy',
                        'description': 'Loop diuretics for volume management',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_B,
                        'actions': [
                            'Start furosemide or bumetanide',
                            'Adjust dose based on volume status',
                            'Monitor daily weights',
                            'Monitor electrolytes and renal function'
                        ]
                    }
                ]
            },

            # COPD
            'copd': {
                'name': 'COPD Management',
                'source': 'GOLD 2024 Guidelines',
                'recommendations': [
                    {
                        'condition': 'COPD Group A',
                        'type': RecommendationType.MEDICATION,
                        'title': 'Initial COPD Therapy - Group A',
                        'description': 'Bronchodilator for symptomatic relief',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_A,
                        'actions': [
                            'Start SABA or SAMA as needed',
                            'Consider LABA or LAMA for persistent symptoms'
                        ]
                    },
                    {
                        'condition': 'COPD with exacerbations',
                        'type': RecommendationType.MEDICATION,
                        'title': 'Triple Therapy for COPD',
                        'description': 'ICS/LABA/LAMA for patients with frequent exacerbations',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_A,
                        'actions': [
                            'Consider triple inhaler therapy',
                            'Options: fluticasone/vilanterol/umeclidinium',
                            'Ensure proper inhaler technique',
                            'Refer for pulmonary rehabilitation'
                        ]
                    }
                ]
            },

            # Asthma
            'asthma': {
                'name': 'Asthma Management',
                'source': 'GINA 2024 Guidelines',
                'recommendations': [
                    {
                        'condition': 'Mild intermittent asthma',
                        'type': RecommendationType.MEDICATION,
                        'title': 'As-Needed ICS-Formoterol',
                        'description': 'Low-dose ICS-formoterol as needed for symptom relief',
                        'strength': RecommendationStrength.STRONG_FOR,
                        'evidence': EvidenceLevel.LEVEL_A,
                        'actions': [
                            'Prescribe budesonide-formoterol inhaler',
                            'Use as needed for symptom relief',
                            'Avoid SABA-only treatment'
                        ]
                    }
                ]
            }
        }

    def get_recommendations(
        self,
        conditions: List[str],
        medications: Optional[List[str]] = None,
        patient_context: Optional[Dict] = None
    ) -> List[ClinicalRecommendation]:
        """Get guideline-based recommendations for conditions."""
        recommendations = []

        for condition in conditions:
            condition_lower = condition.lower()

            # Find matching guidelines
            for guideline_key, guideline in self.guidelines.items():
                if guideline_key in condition_lower or condition_lower in guideline_key:
                    for rec in guideline['recommendations']:
                        # Check if recommendation applies
                        if self._recommendation_applies(rec, patient_context):
                            evidence = ClinicalEvidence(
                                source=guideline['source'],
                                guideline_name=guideline['name'],
                                publication_year=2024,
                                evidence_level=rec['evidence'],
                                citation=guideline['source']
                            )

                            recommendations.append(ClinicalRecommendation(
                                recommendation_id=uuid4(),
                                recommendation_type=rec['type'],
                                title=rec['title'],
                                description=rec['description'],
                                rationale=f"Based on {guideline['source']}",
                                strength=rec['strength'],
                                evidence_level=rec['evidence'],
                                suggested_actions=rec['actions'],
                                alternatives=[],
                                applicable_conditions=[guideline_key],
                                contraindications=[],
                                evidence_citations=[evidence],
                                guideline_source=guideline['source']
                            ))

        return recommendations

    def _recommendation_applies(
        self,
        recommendation: Dict,
        patient_context: Optional[Dict]
    ) -> bool:
        """Check if recommendation applies to patient context."""
        # For now, return True - in production, would check conditions
        return True


class DrugInteractionChecker:
    """Check for drug-drug interactions."""

    def __init__(self):
        self.interaction_database = self._load_interactions()

    def _load_interactions(self) -> Dict[Tuple[str, str], Dict]:
        """Load drug interaction database."""
        interactions = {
            # Major interactions
            ('warfarin', 'aspirin'): {
                'severity': InteractionSeverity.MAJOR,
                'description': 'Increased risk of bleeding',
                'mechanism': 'Aspirin inhibits platelet aggregation, warfarin inhibits clotting factors',
                'clinical_effect': 'Significantly increased bleeding risk, including GI and intracranial bleeding',
                'management': 'Avoid combination unless clearly indicated. If used together, monitor INR closely and watch for bleeding signs.'
            },
            ('warfarin', 'ibuprofen'): {
                'severity': InteractionSeverity.MAJOR,
                'description': 'Increased risk of bleeding and GI ulceration',
                'mechanism': 'NSAIDs inhibit platelet function and cause gastric irritation',
                'clinical_effect': 'Increased risk of GI bleeding and elevated INR',
                'management': 'Avoid NSAIDs in patients on warfarin. Use acetaminophen for pain. If NSAID needed, use gastroprotection.'
            },
            ('metformin', 'contrast_dye'): {
                'severity': InteractionSeverity.MAJOR,
                'description': 'Risk of lactic acidosis',
                'mechanism': 'Contrast media can impair renal function, reducing metformin clearance',
                'clinical_effect': 'Accumulation of metformin leading to lactic acidosis',
                'management': 'Hold metformin 48 hours before and after contrast administration. Check renal function before resuming.'
            },
            ('ssri', 'maoi'): {
                'severity': InteractionSeverity.CONTRAINDICATED,
                'description': 'Risk of serotonin syndrome',
                'mechanism': 'Both classes increase serotonin levels',
                'clinical_effect': 'Life-threatening serotonin syndrome: hyperthermia, rigidity, autonomic instability',
                'management': 'CONTRAINDICATED. Allow 2-week washout between agents.'
            },
            ('ace_inhibitor', 'potassium'): {
                'severity': InteractionSeverity.MODERATE,
                'description': 'Risk of hyperkalemia',
                'mechanism': 'ACE inhibitors reduce aldosterone, decreasing potassium excretion',
                'clinical_effect': 'Elevated serum potassium, cardiac arrhythmias',
                'management': 'Monitor potassium closely. Avoid potassium supplements unless clearly needed.'
            },
            ('statin', 'grapefruit'): {
                'severity': InteractionSeverity.MODERATE,
                'description': 'Increased statin levels',
                'mechanism': 'Grapefruit inhibits CYP3A4, reducing statin metabolism',
                'clinical_effect': 'Increased risk of myopathy and rhabdomyolysis',
                'management': 'Avoid grapefruit with simvastatin, lovastatin, atorvastatin. Pravastatin and rosuvastatin less affected.'
            },
            ('methotrexate', 'nsaid'): {
                'severity': InteractionSeverity.MAJOR,
                'description': 'Increased methotrexate toxicity',
                'mechanism': 'NSAIDs reduce methotrexate renal clearance',
                'clinical_effect': 'Bone marrow suppression, hepatotoxicity, nephrotoxicity',
                'management': 'Avoid NSAIDs with high-dose methotrexate. Use caution with low-dose weekly methotrexate.'
            },
            ('digoxin', 'amiodarone'): {
                'severity': InteractionSeverity.MAJOR,
                'description': 'Increased digoxin toxicity',
                'mechanism': 'Amiodarone inhibits P-glycoprotein and renal elimination of digoxin',
                'clinical_effect': 'Digoxin toxicity: arrhythmias, nausea, visual disturbances',
                'management': 'Reduce digoxin dose by 50% when starting amiodarone. Monitor levels closely.'
            },
            ('clopidogrel', 'omeprazole'): {
                'severity': InteractionSeverity.MODERATE,
                'description': 'Reduced antiplatelet effect',
                'mechanism': 'Omeprazole inhibits CYP2C19, reducing clopidogrel activation',
                'clinical_effect': 'Reduced antiplatelet efficacy, increased cardiovascular events',
                'management': 'Use pantoprazole or H2 blocker instead of omeprazole if PPI needed.'
            },
            ('lithium', 'nsaid'): {
                'severity': InteractionSeverity.MAJOR,
                'description': 'Increased lithium toxicity',
                'mechanism': 'NSAIDs reduce lithium renal clearance',
                'clinical_effect': 'Lithium toxicity: tremor, confusion, seizures',
                'management': 'Monitor lithium levels closely if NSAID needed. Consider sulindac as safer alternative.'
            }
        }
        return interactions

    def check_interactions(
        self,
        medications: List[str]
    ) -> List[DrugInteraction]:
        """Check for interactions among medications."""
        interactions = []
        medications_lower = [m.lower() for m in medications]

        # Check each pair
        for i, med_a in enumerate(medications_lower):
            for med_b in medications_lower[i+1:]:
                interaction = self._find_interaction(med_a, med_b)
                if interaction:
                    interactions.append(interaction)

        return interactions

    def _find_interaction(self, drug_a: str, drug_b: str) -> Optional[DrugInteraction]:
        """Find interaction between two drugs."""
        # Normalize drug names
        drug_a_normalized = self._normalize_drug_name(drug_a)
        drug_b_normalized = self._normalize_drug_name(drug_b)

        # Check both orderings
        key1 = (drug_a_normalized, drug_b_normalized)
        key2 = (drug_b_normalized, drug_a_normalized)

        interaction_data = self.interaction_database.get(key1) or self.interaction_database.get(key2)

        if interaction_data:
            return DrugInteraction(
                interaction_id=uuid4(),
                drug_a=drug_a,
                drug_a_rxnorm='',
                drug_b=drug_b,
                drug_b_rxnorm='',
                severity=interaction_data['severity'],
                description=interaction_data['description'],
                mechanism=interaction_data['mechanism'],
                clinical_effect=interaction_data['clinical_effect'],
                management=interaction_data['management'],
                evidence=[]
            )

        return None

    def _normalize_drug_name(self, drug: str) -> str:
        """Normalize drug name for lookup."""
        # Map brand names and classes
        mappings = {
            'lipitor': 'statin', 'atorvastatin': 'statin', 'simvastatin': 'statin',
            'zocor': 'statin', 'crestor': 'statin', 'rosuvastatin': 'statin',
            'coumadin': 'warfarin',
            'plavix': 'clopidogrel',
            'glucophage': 'metformin',
            'lisinopril': 'ace_inhibitor', 'enalapril': 'ace_inhibitor',
            'benazepril': 'ace_inhibitor', 'ramipril': 'ace_inhibitor',
            'zoloft': 'ssri', 'sertraline': 'ssri', 'prozac': 'ssri',
            'fluoxetine': 'ssri', 'lexapro': 'ssri', 'escitalopram': 'ssri',
            'nardil': 'maoi', 'parnate': 'maoi', 'phenelzine': 'maoi',
            'prilosec': 'omeprazole',
            'advil': 'nsaid', 'ibuprofen': 'nsaid', 'motrin': 'nsaid',
            'aleve': 'nsaid', 'naproxen': 'nsaid',
        }

        drug_lower = drug.lower()
        return mappings.get(drug_lower, drug_lower)


class DiagnosticEngine:
    """Generate differential diagnoses based on symptoms and findings."""

    def __init__(self):
        self.diagnostic_patterns = self._load_diagnostic_patterns()

    def _load_diagnostic_patterns(self) -> Dict[str, Dict]:
        """Load diagnostic pattern database."""
        return {
            'chest_pain': {
                'differentials': [
                    {
                        'condition': 'Acute Coronary Syndrome',
                        'icd10': 'I21.9',
                        'snomed': '394659003',
                        'probability_weight': 0.3,
                        'supporting': ['substernal', 'pressure', 'exertional', 'radiation to arm', 'diaphoresis', 'nausea'],
                        'against': ['pleuritic', 'positional', 'reproducible with palpation'],
                        'red_flags': ['ST elevation', 'troponin elevation', 'hemodynamic instability'],
                        'tests': ['ECG', 'Troponin', 'CXR'],
                        'typical': 'Substernal pressure or squeezing, often with radiation to left arm or jaw, associated with diaphoresis and nausea'
                    },
                    {
                        'condition': 'Pulmonary Embolism',
                        'icd10': 'I26.99',
                        'snomed': '59282003',
                        'probability_weight': 0.15,
                        'supporting': ['pleuritic', 'sudden onset', 'dyspnea', 'tachycardia', 'immobility', 'cancer'],
                        'against': ['gradual onset', 'reproducible'],
                        'red_flags': ['hypoxia', 'hypotension', 'RV strain'],
                        'tests': ['D-dimer', 'CT angiography', 'V/Q scan'],
                        'typical': 'Sudden onset pleuritic chest pain with dyspnea, tachycardia'
                    },
                    {
                        'condition': 'Pneumothorax',
                        'icd10': 'J93.9',
                        'snomed': '36118008',
                        'probability_weight': 0.1,
                        'supporting': ['sudden onset', 'pleuritic', 'dyspnea', 'tall thin male', 'smoking'],
                        'against': ['gradual onset', 'exertional'],
                        'red_flags': ['hypotension', 'tracheal deviation'],
                        'tests': ['CXR', 'CT chest'],
                        'typical': 'Sudden onset sharp pleuritic chest pain with dyspnea'
                    },
                    {
                        'condition': 'Musculoskeletal Pain',
                        'icd10': 'R07.89',
                        'snomed': '139497007',
                        'probability_weight': 0.25,
                        'supporting': ['reproducible with palpation', 'positional', 'history of trauma', 'localized'],
                        'against': ['exertional', 'radiation', 'diaphoresis'],
                        'red_flags': [],
                        'tests': ['Clinical exam'],
                        'typical': 'Chest wall tenderness reproducible with palpation'
                    },
                    {
                        'condition': 'GERD',
                        'icd10': 'K21.0',
                        'snomed': '235595009',
                        'probability_weight': 0.2,
                        'supporting': ['burning', 'postprandial', 'worse lying down', 'relieved by antacids'],
                        'against': ['exertional', 'sudden onset'],
                        'red_flags': ['dysphagia', 'weight loss'],
                        'tests': ['Trial of PPI', 'EGD if red flags'],
                        'typical': 'Burning retrosternal discomfort, worse after meals and lying down'
                    }
                ]
            },
            'headache': {
                'differentials': [
                    {
                        'condition': 'Tension-type Headache',
                        'icd10': 'G44.209',
                        'snomed': '398057008',
                        'probability_weight': 0.4,
                        'supporting': ['bilateral', 'pressing', 'mild-moderate', 'stress'],
                        'against': ['pulsating', 'severe', 'nausea'],
                        'red_flags': [],
                        'tests': ['Clinical diagnosis'],
                        'typical': 'Bilateral pressing headache, mild to moderate intensity, not worsened by activity'
                    },
                    {
                        'condition': 'Migraine',
                        'icd10': 'G43.909',
                        'snomed': '37796009',
                        'probability_weight': 0.3,
                        'supporting': ['unilateral', 'pulsating', 'nausea', 'photophobia', 'aura'],
                        'against': ['bilateral', 'pressing'],
                        'red_flags': ['first migraine over 50', 'sudden onset', 'fever'],
                        'tests': ['Clinical diagnosis', 'MRI if red flags'],
                        'typical': 'Unilateral pulsating headache with nausea, photophobia, phonophobia'
                    },
                    {
                        'condition': 'Subarachnoid Hemorrhage',
                        'icd10': 'I60.9',
                        'snomed': '21454007',
                        'probability_weight': 0.05,
                        'supporting': ['thunderclap', 'worst headache', 'sudden', 'neck stiffness'],
                        'against': ['gradual onset', 'chronic'],
                        'red_flags': ['altered consciousness', 'focal deficits', 'fever'],
                        'tests': ['CT head without contrast', 'LP if CT negative'],
                        'typical': 'Sudden onset thunderclap headache, worst headache of life'
                    }
                ]
            },
            'shortness_of_breath': {
                'differentials': [
                    {
                        'condition': 'Heart Failure Exacerbation',
                        'icd10': 'I50.9',
                        'snomed': '84114007',
                        'probability_weight': 0.25,
                        'supporting': ['orthopnea', 'PND', 'edema', 'JVD', 'history of CHF'],
                        'against': ['wheezing', 'fever'],
                        'red_flags': ['hypoxia', 'hypotension'],
                        'tests': ['BNP', 'CXR', 'Echo'],
                        'typical': 'Progressive dyspnea with orthopnea, PND, and peripheral edema'
                    },
                    {
                        'condition': 'COPD Exacerbation',
                        'icd10': 'J44.1',
                        'snomed': '195951007',
                        'probability_weight': 0.25,
                        'supporting': ['smoking history', 'productive cough', 'wheezing', 'known COPD'],
                        'against': ['orthopnea without wheezing', 'edema'],
                        'red_flags': ['severe hypoxia', 'altered mental status'],
                        'tests': ['ABG', 'CXR', 'Spirometry'],
                        'typical': 'Increased dyspnea, cough, and sputum production in patient with COPD'
                    },
                    {
                        'condition': 'Pneumonia',
                        'icd10': 'J18.9',
                        'snomed': '233604007',
                        'probability_weight': 0.2,
                        'supporting': ['fever', 'productive cough', 'pleuritic pain', 'crackles'],
                        'against': ['chronic', 'no fever'],
                        'red_flags': ['hypoxia', 'sepsis'],
                        'tests': ['CXR', 'CBC', 'Procalcitonin'],
                        'typical': 'Fever, productive cough, dyspnea with focal crackles'
                    }
                ]
            }
        }

    def generate_differentials(
        self,
        chief_complaint: str,
        symptoms: List[str],
        patient_context: Optional[Dict] = None
    ) -> List[DiagnosticSuggestion]:
        """Generate differential diagnosis list."""
        differentials = []
        complaint_lower = chief_complaint.lower()
        symptoms_lower = [s.lower() for s in symptoms]

        # Find matching pattern
        for pattern_key, pattern_data in self.diagnostic_patterns.items():
            if pattern_key in complaint_lower:
                for diff in pattern_data['differentials']:
                    # Calculate probability based on supporting/against findings
                    supporting_count = sum(
                        1 for f in diff['supporting']
                        if any(f in s for s in symptoms_lower) or f in complaint_lower
                    )
                    against_count = sum(
                        1 for f in diff['against']
                        if any(f in s for s in symptoms_lower) or f in complaint_lower
                    )

                    # Adjust probability
                    base_prob = diff['probability_weight']
                    adjusted_prob = base_prob * (1 + 0.1 * supporting_count - 0.15 * against_count)
                    adjusted_prob = max(0.01, min(0.95, adjusted_prob))

                    differentials.append(DiagnosticSuggestion(
                        suggestion_id=uuid4(),
                        condition_name=diff['condition'],
                        icd10_code=diff['icd10'],
                        snomed_code=diff['snomed'],
                        probability=adjusted_prob,
                        supporting_findings=[
                            f for f in diff['supporting']
                            if any(f in s for s in symptoms_lower) or f in complaint_lower
                        ],
                        against_findings=[
                            f for f in diff['against']
                            if any(f in s for s in symptoms_lower) or f in complaint_lower
                        ],
                        recommended_tests=diff['tests'],
                        red_flags=diff['red_flags'],
                        typical_presentation=diff['typical']
                    ))

        # Sort by probability
        differentials.sort(key=lambda x: x.probability, reverse=True)
        return differentials[:5]


class ClinicalDecisionIntelligence:
    """Main clinical decision intelligence service."""

    def __init__(self):
        self.guideline_engine = ClinicalGuidelineEngine()
        self.interaction_checker = DrugInteractionChecker()
        self.diagnostic_engine = DiagnosticEngine()

    async def analyze(
        self,
        patient_context: Dict[str, Any],
        conditions: Optional[List[str]] = None,
        medications: Optional[List[str]] = None,
        chief_complaint: Optional[str] = None,
        symptoms: Optional[List[str]] = None,
        labs: Optional[Dict[str, Any]] = None,
        vitals: Optional[Dict[str, Any]] = None
    ) -> DecisionSupportResult:
        """Perform comprehensive clinical decision support analysis."""
        import time
        start_time = time.time()

        alerts: List[ClinicalAlert] = []

        # Get treatment recommendations
        treatment_recommendations = []
        if conditions:
            treatment_recommendations = self.guideline_engine.get_recommendations(
                conditions, medications, patient_context
            )

        # Check drug interactions
        drug_interactions = []
        if medications:
            drug_interactions = self.interaction_checker.check_interactions(medications)
            for interaction in drug_interactions:
                severity_map = {
                    InteractionSeverity.CONTRAINDICATED: 'critical',
                    InteractionSeverity.MAJOR: 'critical',
                    InteractionSeverity.MODERATE: 'warning',
                    InteractionSeverity.MINOR: 'info'
                }
                alerts.append(ClinicalAlert(
                    alert_id=uuid4(),
                    category=AlertCategory.DRUG_INTERACTION,
                    severity=severity_map.get(interaction.severity, 'warning'),
                    title=f"{interaction.drug_a} - {interaction.drug_b} Interaction",
                    message=interaction.description,
                    rationale=interaction.mechanism,
                    suggested_action=interaction.management,
                    override_reason_required=interaction.severity in [InteractionSeverity.CONTRAINDICATED, InteractionSeverity.MAJOR]
                ))

        # Generate differential diagnoses
        diagnostic_suggestions = []
        if chief_complaint:
            diagnostic_suggestions = self.diagnostic_engine.generate_differentials(
                chief_complaint,
                symptoms or [],
                patient_context
            )

        # Generate monitoring recommendations
        monitoring_recommendations = self._generate_monitoring_recommendations(
            conditions, medications, labs
        )

        # Generate referral suggestions
        referral_suggestions = self._generate_referral_suggestions(
            conditions, diagnostic_suggestions
        )

        # Generate summary
        summary = self._generate_summary(
            treatment_recommendations,
            diagnostic_suggestions,
            alerts
        )

        # Identify priority actions
        priority_actions = self._identify_priority_actions(
            alerts, treatment_recommendations, diagnostic_suggestions
        )

        processing_time = (time.time() - start_time) * 1000

        return DecisionSupportResult(
            result_id=uuid4(),
            patient_context=patient_context,
            treatment_recommendations=treatment_recommendations,
            diagnostic_suggestions=diagnostic_suggestions,
            referral_suggestions=referral_suggestions,
            monitoring_recommendations=monitoring_recommendations,
            alerts=alerts,
            drug_interactions=drug_interactions,
            summary=summary,
            priority_actions=priority_actions,
            processing_time_ms=processing_time,
            created_at=datetime.now(timezone.utc)
        )

    def _generate_monitoring_recommendations(
        self,
        conditions: Optional[List[str]],
        medications: Optional[List[str]],
        labs: Optional[Dict]
    ) -> List[ClinicalRecommendation]:
        """Generate lab/monitoring recommendations."""
        recommendations = []

        # Monitoring based on medications
        medication_monitoring = {
            'warfarin': {'test': 'INR', 'frequency': 'Weekly until stable, then monthly'},
            'metformin': {'test': 'Creatinine/eGFR', 'frequency': 'Annually'},
            'ace_inhibitor': {'test': 'Potassium, Creatinine', 'frequency': 'Within 2 weeks of starting, then annually'},
            'statin': {'test': 'Lipid panel, LFTs', 'frequency': 'Annually'},
            'lithium': {'test': 'Lithium level, TSH, Creatinine', 'frequency': 'Every 3-6 months'},
        }

        if medications:
            for med in medications:
                med_lower = med.lower()
                for key, monitoring in medication_monitoring.items():
                    if key in med_lower:
                        recommendations.append(ClinicalRecommendation(
                            recommendation_id=uuid4(),
                            recommendation_type=RecommendationType.MONITORING,
                            title=f"Monitor {monitoring['test']} for {med}",
                            description=f"Regular monitoring required for {med}",
                            rationale=f"Standard monitoring for patients on {med}",
                            strength=RecommendationStrength.STRONG_FOR,
                            evidence_level=EvidenceLevel.LEVEL_A,
                            suggested_actions=[
                                f"Order {monitoring['test']}",
                                f"Frequency: {monitoring['frequency']}"
                            ],
                            alternatives=[],
                            applicable_conditions=[],
                            contraindications=[],
                            evidence_citations=[]
                        ))

        return recommendations

    def _generate_referral_suggestions(
        self,
        conditions: Optional[List[str]],
        differentials: List[DiagnosticSuggestion]
    ) -> List[ClinicalRecommendation]:
        """Generate specialist referral suggestions."""
        suggestions = []

        # Referral triggers based on conditions
        referral_map = {
            'heart failure': 'Cardiology',
            'chronic kidney disease': 'Nephrology',
            'copd': 'Pulmonology',
            'cancer': 'Oncology',
            'depression': 'Psychiatry',
            'diabetes': 'Endocrinology (if uncontrolled)',
        }

        if conditions:
            for condition in conditions:
                condition_lower = condition.lower()
                for trigger, specialty in referral_map.items():
                    if trigger in condition_lower:
                        suggestions.append(ClinicalRecommendation(
                            recommendation_id=uuid4(),
                            recommendation_type=RecommendationType.REFERRAL,
                            title=f"Consider {specialty} Referral",
                            description=f"Referral to {specialty} may benefit patient with {condition}",
                            rationale=f"Specialist management often improves outcomes for {trigger}",
                            strength=RecommendationStrength.MODERATE_FOR,
                            evidence_level=EvidenceLevel.LEVEL_B,
                            suggested_actions=[
                                f"Refer to {specialty}",
                                "Provide relevant records and history"
                            ],
                            alternatives=[],
                            applicable_conditions=[condition],
                            contraindications=[],
                            evidence_citations=[]
                        ))

        return suggestions

    def _generate_summary(
        self,
        recommendations: List[ClinicalRecommendation],
        differentials: List[DiagnosticSuggestion],
        alerts: List[ClinicalAlert]
    ) -> str:
        """Generate clinical decision support summary."""
        parts = []

        critical_alerts = [a for a in alerts if a.severity == 'critical']
        if critical_alerts:
            parts.append(f"CRITICAL ALERTS: {len(critical_alerts)} require immediate attention.")

        if differentials:
            top_diff = differentials[0]
            parts.append(f"Top differential: {top_diff.condition_name} ({top_diff.probability:.0%} probability).")

        if recommendations:
            parts.append(f"{len(recommendations)} guideline-based recommendations generated.")

        return ' '.join(parts) if parts else "No significant clinical decision support findings."

    def _identify_priority_actions(
        self,
        alerts: List[ClinicalAlert],
        recommendations: List[ClinicalRecommendation],
        differentials: List[DiagnosticSuggestion]
    ) -> List[str]:
        """Identify priority actions."""
        actions = []

        # Critical alerts first
        for alert in alerts:
            if alert.severity == 'critical':
                actions.append(f"URGENT: {alert.suggested_action}")

        # Red flags from differentials
        for diff in differentials[:3]:
            if diff.red_flags:
                actions.append(f"Watch for red flags: {', '.join(diff.red_flags[:3])}")

        # Top recommendations
        for rec in recommendations[:3]:
            if rec.strength in [RecommendationStrength.STRONG_FOR]:
                actions.append(rec.suggested_actions[0] if rec.suggested_actions else rec.title)

        return actions[:5]


# Global instance
clinical_decision_intelligence = ClinicalDecisionIntelligence()
