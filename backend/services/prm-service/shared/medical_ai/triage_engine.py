"""
Advanced Medical Triage Engine

EPIC-010: Medical AI Capabilities
US-010.1: AI-Powered Medical Triage

Comprehensive symptom analysis with:
- Natural language symptom processing
- Red flag identification (100% sensitivity target)
- Urgency classification
- Department routing
- Clinical explainability
- Evidence-based rationale
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4, UUID
import re
import hashlib


class UrgencyLevel(str, Enum):
    """Triage urgency levels based on ESI (Emergency Severity Index)."""
    EMERGENCY = "emergency"      # ESI Level 1: Immediate, life-threatening
    URGENT = "urgent"            # ESI Level 2: High risk, time-sensitive
    LESS_URGENT = "less_urgent"  # ESI Level 3: Multiple resources needed
    SEMI_URGENT = "semi_urgent"  # ESI Level 4: One resource expected
    NON_URGENT = "non_urgent"    # ESI Level 5: No resources expected
    SELF_CARE = "self_care"      # Can manage at home


class BodySystem(str, Enum):
    """Body system categories for triage."""
    NEUROLOGICAL = "neurological"
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    MUSCULOSKELETAL = "musculoskeletal"
    GENITOURINARY = "genitourinary"
    DERMATOLOGICAL = "dermatological"
    OPHTHALMOLOGICAL = "ophthalmological"
    ENT = "ent"
    PSYCHIATRIC = "psychiatric"
    ENDOCRINE = "endocrine"
    HEMATOLOGICAL = "hematological"
    IMMUNOLOGICAL = "immunological"
    GENERAL = "general"


class Department(str, Enum):
    """Clinical department routing."""
    EMERGENCY = "emergency"
    URGENT_CARE = "urgent_care"
    PRIMARY_CARE = "primary_care"
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    PULMONOLOGY = "pulmonology"
    GASTROENTEROLOGY = "gastroenterology"
    ORTHOPEDICS = "orthopedics"
    DERMATOLOGY = "dermatology"
    OPHTHALMOLOGY = "ophthalmology"
    ENT = "ent"
    PSYCHIATRY = "psychiatry"
    OB_GYN = "ob_gyn"
    UROLOGY = "urology"
    ONCOLOGY = "oncology"
    PEDIATRICS = "pediatrics"
    GERIATRICS = "geriatrics"


@dataclass
class Symptom:
    """Parsed symptom with attributes."""
    name: str
    severity: int  # 1-10
    duration: Optional[str] = None
    duration_hours: Optional[float] = None
    onset: Optional[str] = None  # sudden, gradual
    location: Optional[str] = None
    character: Optional[str] = None  # sharp, dull, burning
    radiation: Optional[str] = None
    aggravating_factors: List[str] = field(default_factory=list)
    relieving_factors: List[str] = field(default_factory=list)
    associated_symptoms: List[str] = field(default_factory=list)
    body_system: Optional[BodySystem] = None
    raw_text: Optional[str] = None


@dataclass
class RedFlag:
    """Critical clinical red flag."""
    name: str
    description: str
    body_system: BodySystem
    urgency: UrgencyLevel
    rationale: str
    action_required: str
    evidence_source: str
    sensitivity: float = 1.0  # Target 100% sensitivity


@dataclass
class TriageDecision:
    """Triage decision with full explainability."""
    decision_id: UUID
    urgency_level: UrgencyLevel
    urgency_score: int  # 0-100
    confidence_score: float  # 0.0-1.0

    # Clinical assessment
    primary_concern: str
    differential_considerations: List[str]
    body_systems_involved: List[BodySystem]

    # Red flags
    red_flags_identified: List[RedFlag]
    red_flag_count: int

    # Routing
    recommended_department: Department
    alternative_departments: List[Department]
    timeframe: str  # "Immediate", "Within 2 hours", "Within 24 hours", etc.
    care_setting: str  # "Emergency", "Urgent Care", "Primary Care", "Home"

    # Recommendations
    recommended_actions: List[str]
    self_care_advice: List[str]
    warning_signs_to_watch: List[str]

    # Explainability
    decision_rationale: str
    contributing_factors: List[Dict[str, Any]]
    evidence_citations: List[str]
    decision_path: List[str]

    # Disclaimers
    disclaimer: str
    requires_human_review: bool

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SymptomAnalyzer:
    """Advanced symptom analysis using NLP."""

    # Duration patterns
    DURATION_PATTERNS = [
        (r'(\d+)\s*minute', 1/60),
        (r'(\d+)\s*hour', 1),
        (r'(\d+)\s*day', 24),
        (r'(\d+)\s*week', 168),
        (r'(\d+)\s*month', 720),
        (r'few\s*minute', 0.1),
        (r'few\s*hour', 3),
        (r'few\s*day', 72),
        (r'since\s*yesterday', 24),
        (r'since\s*this\s*morning', 8),
        (r'just\s*started', 0.5),
        (r'all\s*day', 12),
        (r'overnight', 8),
    ]

    # Severity indicators
    SEVERITY_MODIFIERS = {
        'worst': 10, 'unbearable': 10, 'excruciating': 10, 'extreme': 9,
        'severe': 8, 'terrible': 8, 'awful': 8, 'intense': 8,
        'significant': 7, 'considerable': 7, 'bad': 7,
        'moderate': 5, 'medium': 5, 'noticeable': 5,
        'mild': 3, 'slight': 3, 'minor': 3, 'little': 2,
        'barely': 1, 'hardly': 1
    }

    # Body system mapping
    SYMPTOM_BODY_SYSTEM_MAP = {
        BodySystem.NEUROLOGICAL: [
            'headache', 'migraine', 'dizzy', 'vertigo', 'numbness', 'tingling',
            'weakness', 'paralysis', 'confusion', 'memory', 'seizure', 'tremor',
            'vision change', 'speech', 'balance', 'coordination'
        ],
        BodySystem.CARDIOVASCULAR: [
            'chest pain', 'palpitation', 'racing heart', 'shortness of breath',
            'swelling', 'edema', 'leg pain', 'arm pain', 'jaw pain', 'fainting',
            'syncope', 'blood pressure', 'cold extremities'
        ],
        BodySystem.RESPIRATORY: [
            'cough', 'wheezing', 'breathing', 'dyspnea', 'sputum', 'phlegm',
            'congestion', 'runny nose', 'sore throat', 'chest tightness',
            'stridor', 'hemoptysis', 'bloody cough'
        ],
        BodySystem.GASTROINTESTINAL: [
            'nausea', 'vomiting', 'diarrhea', 'constipation', 'abdominal pain',
            'stomach', 'bloating', 'heartburn', 'acid reflux', 'blood in stool',
            'rectal bleeding', 'appetite', 'weight loss', 'jaundice'
        ],
        BodySystem.MUSCULOSKELETAL: [
            'back pain', 'joint pain', 'muscle pain', 'stiffness', 'swollen joint',
            'sprain', 'strain', 'fracture', 'bone pain', 'neck pain', 'shoulder',
            'knee', 'hip', 'ankle', 'wrist'
        ],
        BodySystem.GENITOURINARY: [
            'urination', 'burning urination', 'frequent urination', 'blood in urine',
            'kidney', 'flank pain', 'pelvic pain', 'discharge', 'incontinence'
        ],
        BodySystem.DERMATOLOGICAL: [
            'rash', 'itch', 'hives', 'swelling', 'wound', 'bruise', 'burn',
            'skin change', 'lesion', 'mole', 'discoloration'
        ],
        BodySystem.PSYCHIATRIC: [
            'anxiety', 'depression', 'panic', 'stress', 'sleep', 'insomnia',
            'suicidal', 'self-harm', 'hallucination', 'paranoia', 'mood'
        ],
        BodySystem.GENERAL: [
            'fever', 'fatigue', 'tired', 'weakness', 'weight', 'appetite',
            'night sweats', 'chills', 'malaise'
        ]
    }

    def analyze_symptom(self, text: str, reported_severity: Optional[int] = None) -> Symptom:
        """Analyze symptom text to extract structured information."""
        text_lower = text.lower()

        # Extract duration
        duration, duration_hours = self._extract_duration(text_lower)

        # Determine severity
        severity = self._determine_severity(text_lower, reported_severity)

        # Extract onset
        onset = self._extract_onset(text_lower)

        # Extract location
        location = self._extract_location(text_lower)

        # Extract character
        character = self._extract_character(text_lower)

        # Determine body system
        body_system = self._determine_body_system(text_lower)

        # Extract associated symptoms
        associated = self._extract_associated_symptoms(text_lower)

        return Symptom(
            name=self._extract_symptom_name(text),
            severity=severity,
            duration=duration,
            duration_hours=duration_hours,
            onset=onset,
            location=location,
            character=character,
            body_system=body_system,
            associated_symptoms=associated,
            raw_text=text
        )

    def _extract_duration(self, text: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract duration from text."""
        for pattern, hours_multiplier in self.DURATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = int(match.group(1)) if match.groups() else 1
                    return match.group(0), value * hours_multiplier
                except (IndexError, ValueError):
                    return match.group(0), hours_multiplier
        return None, None

    def _determine_severity(self, text: str, reported: Optional[int]) -> int:
        """Determine severity from text or reported value."""
        if reported is not None:
            return max(1, min(10, reported))

        for modifier, severity in self.SEVERITY_MODIFIERS.items():
            if modifier in text:
                return severity

        # Default to moderate if no modifier found
        return 5

    def _extract_onset(self, text: str) -> Optional[str]:
        """Extract onset pattern."""
        if any(word in text for word in ['sudden', 'suddenly', 'abrupt', 'immediately']):
            return 'sudden'
        elif any(word in text for word in ['gradual', 'gradually', 'slowly', 'progressive']):
            return 'gradual'
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract anatomical location."""
        locations = [
            'head', 'forehead', 'temple', 'neck', 'throat', 'chest', 'back',
            'upper back', 'lower back', 'abdomen', 'stomach', 'left', 'right',
            'arm', 'leg', 'hand', 'foot', 'shoulder', 'elbow', 'wrist', 'hip',
            'knee', 'ankle', 'eye', 'ear', 'jaw'
        ]
        for loc in locations:
            if loc in text:
                return loc
        return None

    def _extract_character(self, text: str) -> Optional[str]:
        """Extract pain/symptom character."""
        characters = {
            'sharp': ['sharp', 'stabbing', 'piercing', 'cutting'],
            'dull': ['dull', 'aching', 'deep'],
            'burning': ['burning', 'hot', 'warm'],
            'throbbing': ['throbbing', 'pulsating', 'pounding'],
            'cramping': ['cramping', 'crampy', 'spasm'],
            'pressure': ['pressure', 'heavy', 'squeezing', 'tightness'],
            'shooting': ['shooting', 'radiating', 'electric']
        }
        for char_type, keywords in characters.items():
            if any(kw in text for kw in keywords):
                return char_type
        return None

    def _determine_body_system(self, text: str) -> Optional[BodySystem]:
        """Determine the primary body system."""
        for system, keywords in self.SYMPTOM_BODY_SYSTEM_MAP.items():
            if any(kw in text for kw in keywords):
                return system
        return BodySystem.GENERAL

    def _extract_symptom_name(self, text: str) -> str:
        """Extract the core symptom name."""
        # Remove modifiers and extract core symptom
        for modifier in self.SEVERITY_MODIFIERS.keys():
            text = re.sub(rf'\b{modifier}\b', '', text, flags=re.IGNORECASE)
        return text.strip()[:100]

    def _extract_associated_symptoms(self, text: str) -> List[str]:
        """Extract mentioned associated symptoms."""
        associated = []
        symptom_keywords = [
            'nausea', 'vomiting', 'fever', 'chills', 'sweating', 'dizziness',
            'fatigue', 'weakness', 'numbness', 'tingling', 'shortness of breath'
        ]
        for symptom in symptom_keywords:
            if symptom in text.lower():
                associated.append(symptom)
        return associated


class RedFlagDetector:
    """Detect critical clinical red flags with 100% sensitivity target."""

    def __init__(self):
        self.red_flags = self._initialize_red_flags()

    def _initialize_red_flags(self) -> Dict[str, RedFlag]:
        """Initialize comprehensive red flag database."""
        return {
            # Neurological Red Flags
            'sudden_severe_headache': RedFlag(
                name="Sudden Severe Headache",
                description="Thunderclap headache - worst headache of life",
                body_system=BodySystem.NEUROLOGICAL,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="May indicate subarachnoid hemorrhage, aneurysm rupture",
                action_required="Immediate CT head and neurosurgical evaluation",
                evidence_source="AHA/ASA Stroke Guidelines 2019"
            ),
            'focal_neurological_deficit': RedFlag(
                name="Focal Neurological Deficit",
                description="Sudden weakness, numbness, speech difficulty, vision loss",
                body_system=BodySystem.NEUROLOGICAL,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="Signs of acute stroke - time-critical for intervention",
                action_required="Activate stroke protocol, immediate CT/MRI",
                evidence_source="AHA/ASA Stroke Guidelines 2019"
            ),
            'altered_consciousness': RedFlag(
                name="Altered Level of Consciousness",
                description="Confusion, lethargy, unresponsiveness, sudden behavior change",
                body_system=BodySystem.NEUROLOGICAL,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="May indicate stroke, infection, metabolic emergency, overdose",
                action_required="Immediate evaluation, glucose check, vital signs",
                evidence_source="ACEP Clinical Policy 2014"
            ),
            'seizure_first': RedFlag(
                name="First-Time Seizure",
                description="New onset seizure activity in adult",
                body_system=BodySystem.NEUROLOGICAL,
                urgency=UrgencyLevel.URGENT,
                rationale="Requires workup for underlying cause",
                action_required="CT head, labs, neurology referral",
                evidence_source="AAN Practice Parameters 2015"
            ),

            # Cardiovascular Red Flags
            'chest_pain_cardiac': RedFlag(
                name="Cardiac Chest Pain",
                description="Chest pain with pressure, radiating to arm/jaw, with SOB/diaphoresis",
                body_system=BodySystem.CARDIOVASCULAR,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="Classic presentation of acute coronary syndrome",
                action_required="ECG within 10 minutes, cardiac markers, aspirin",
                evidence_source="AHA/ACC STEMI Guidelines 2020"
            ),
            'severe_hypertension': RedFlag(
                name="Severe Hypertension",
                description="BP >180/120 with symptoms (headache, chest pain, vision changes)",
                body_system=BodySystem.CARDIOVASCULAR,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="Hypertensive emergency risking end-organ damage",
                action_required="Immediate BP control, organ function assessment",
                evidence_source="JNC 8 Guidelines"
            ),
            'syncope_cardiac': RedFlag(
                name="Syncope with Cardiac Features",
                description="Fainting with palpitations, exertional, or family history sudden death",
                body_system=BodySystem.CARDIOVASCULAR,
                urgency=UrgencyLevel.URGENT,
                rationale="Risk of arrhythmia, structural heart disease",
                action_required="ECG, cardiac monitoring, echocardiogram",
                evidence_source="ESC Syncope Guidelines 2018"
            ),
            'leg_swelling_asymmetric': RedFlag(
                name="Unilateral Leg Swelling",
                description="Asymmetric leg swelling with pain, especially after immobility",
                body_system=BodySystem.CARDIOVASCULAR,
                urgency=UrgencyLevel.URGENT,
                rationale="High suspicion for deep vein thrombosis",
                action_required="D-dimer, venous duplex ultrasound",
                evidence_source="ACCP VTE Guidelines 2016"
            ),

            # Respiratory Red Flags
            'severe_respiratory_distress': RedFlag(
                name="Severe Respiratory Distress",
                description="Extreme difficulty breathing, unable to speak in sentences, tripoding",
                body_system=BodySystem.RESPIRATORY,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="Respiratory failure imminent",
                action_required="Oxygen, prepare for intubation, CXR, ABG",
                evidence_source="GOLD COPD Guidelines 2023"
            ),
            'hemoptysis_significant': RedFlag(
                name="Significant Hemoptysis",
                description="Coughing up blood more than streaks",
                body_system=BodySystem.RESPIRATORY,
                urgency=UrgencyLevel.URGENT,
                rationale="May indicate malignancy, PE, TB, or vascular abnormality",
                action_required="CXR, CT chest, possible bronchoscopy",
                evidence_source="ACCP Hemoptysis Guidelines 2018"
            ),
            'sudden_pleuritic_pain': RedFlag(
                name="Sudden Pleuritic Chest Pain with SOB",
                description="Sharp chest pain worse with breathing, sudden onset SOB",
                body_system=BodySystem.RESPIRATORY,
                urgency=UrgencyLevel.URGENT,
                rationale="Concerning for pulmonary embolism",
                action_required="D-dimer, CT pulmonary angiography",
                evidence_source="PIOPED III Criteria"
            ),

            # Gastrointestinal Red Flags
            'gi_bleeding_acute': RedFlag(
                name="Acute GI Bleeding",
                description="Vomiting blood, black tarry stools, blood in stool",
                body_system=BodySystem.GASTROINTESTINAL,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="Risk of hemorrhagic shock",
                action_required="IV access, type and cross, emergent GI consult",
                evidence_source="ACG GI Bleeding Guidelines 2021"
            ),
            'severe_abdominal_pain': RedFlag(
                name="Severe Abdominal Pain with Red Flags",
                description="Rigid abdomen, rebound tenderness, fever, tachycardia",
                body_system=BodySystem.GASTROINTESTINAL,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="May indicate peritonitis, perforation, obstruction",
                action_required="Surgical evaluation, CT abdomen, labs",
                evidence_source="SAGES Acute Abdomen Guidelines"
            ),

            # Infectious Disease Red Flags
            'sepsis_criteria': RedFlag(
                name="Suspected Sepsis",
                description="Fever with tachycardia, hypotension, altered mental status",
                body_system=BodySystem.GENERAL,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="Sepsis mortality increases with each hour of delayed treatment",
                action_required="Blood cultures, lactate, antibiotics within 1 hour",
                evidence_source="Surviving Sepsis Campaign 2021"
            ),
            'meningitis_signs': RedFlag(
                name="Meningitis Signs",
                description="Severe headache with fever, neck stiffness, photophobia",
                body_system=BodySystem.NEUROLOGICAL,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="Bacterial meningitis is rapidly fatal without treatment",
                action_required="Lumbar puncture, empiric antibiotics, steroids",
                evidence_source="IDSA Bacterial Meningitis Guidelines 2017"
            ),

            # Psychiatric Red Flags
            'suicidal_ideation': RedFlag(
                name="Suicidal Ideation",
                description="Thoughts of self-harm, suicide plan, hopelessness",
                body_system=BodySystem.PSYCHIATRIC,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="Immediate risk to patient safety",
                action_required="Safety assessment, 1:1 observation, psychiatric evaluation",
                evidence_source="APA Suicide Assessment Guidelines 2016"
            ),
            'acute_psychosis': RedFlag(
                name="Acute Psychosis",
                description="Hallucinations, delusions, severely disorganized behavior",
                body_system=BodySystem.PSYCHIATRIC,
                urgency=UrgencyLevel.URGENT,
                rationale="Risk to self and others, may have medical cause",
                action_required="Medical workup, psychiatric evaluation, safe environment",
                evidence_source="APA Schizophrenia Guidelines 2021"
            ),

            # Obstetric Red Flags
            'ectopic_pregnancy_signs': RedFlag(
                name="Possible Ectopic Pregnancy",
                description="Pelvic pain with vaginal bleeding in woman of childbearing age",
                body_system=BodySystem.GENITOURINARY,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="Ruptured ectopic can cause life-threatening hemorrhage",
                action_required="Pregnancy test, transvaginal ultrasound, GYN consult",
                evidence_source="ACOG Practice Bulletin 2018"
            ),

            # Anaphylaxis
            'anaphylaxis': RedFlag(
                name="Anaphylaxis",
                description="Rapid onset hives, swelling, difficulty breathing after exposure",
                body_system=BodySystem.IMMUNOLOGICAL,
                urgency=UrgencyLevel.EMERGENCY,
                rationale="Can progress to cardiovascular collapse within minutes",
                action_required="Epinephrine IM immediately, airway management",
                evidence_source="WAO Anaphylaxis Guidelines 2020"
            )
        }

    def detect_red_flags(
        self,
        symptoms: List[Symptom],
        vitals: Optional[Dict[str, Any]] = None,
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
        medical_history: Optional[List[str]] = None,
        chief_complaint: Optional[str] = None
    ) -> List[RedFlag]:
        """Detect all applicable red flags with 100% sensitivity target."""
        detected = []
        all_text = ' '.join([s.raw_text or s.name for s in symptoms]).lower()
        if chief_complaint:
            all_text += ' ' + chief_complaint.lower()

        # Check each red flag pattern
        detected.extend(self._check_neurological_red_flags(symptoms, all_text, vitals))
        detected.extend(self._check_cardiovascular_red_flags(symptoms, all_text, vitals))
        detected.extend(self._check_respiratory_red_flags(symptoms, all_text, vitals))
        detected.extend(self._check_gi_red_flags(symptoms, all_text, vitals))
        detected.extend(self._check_infectious_red_flags(symptoms, all_text, vitals))
        detected.extend(self._check_psychiatric_red_flags(symptoms, all_text))
        detected.extend(self._check_obstetric_red_flags(symptoms, all_text, patient_sex, patient_age))
        detected.extend(self._check_allergic_red_flags(symptoms, all_text))

        return detected

    def _check_neurological_red_flags(
        self, symptoms: List[Symptom], text: str, vitals: Optional[Dict]
    ) -> List[RedFlag]:
        """Check neurological red flags."""
        detected = []

        # Thunderclap headache
        if any(s.body_system == BodySystem.NEUROLOGICAL for s in symptoms):
            if ('worst' in text or 'sudden' in text) and 'headache' in text:
                detected.append(self.red_flags['sudden_severe_headache'])

        # Focal deficits (stroke signs)
        stroke_keywords = ['weakness', 'numbness', 'face droop', 'slurred speech',
                         'vision loss', 'can\'t speak', 'arm drift']
        if any(kw in text for kw in stroke_keywords):
            if any('sudden' in (s.onset or '') for s in symptoms) or 'sudden' in text:
                detected.append(self.red_flags['focal_neurological_deficit'])

        # Altered consciousness
        aoc_keywords = ['confused', 'confusion', 'lethargy', 'unresponsive', 'passed out',
                       'not making sense', 'acting strange', 'disoriented']
        if any(kw in text for kw in aoc_keywords):
            detected.append(self.red_flags['altered_consciousness'])

        # First seizure
        if 'seizure' in text and 'first' in text:
            detected.append(self.red_flags['seizure_first'])

        return detected

    def _check_cardiovascular_red_flags(
        self, symptoms: List[Symptom], text: str, vitals: Optional[Dict]
    ) -> List[RedFlag]:
        """Check cardiovascular red flags."""
        detected = []

        # Cardiac chest pain
        cardiac_indicators = ['pressure', 'squeezing', 'elephant', 'arm pain', 'jaw pain',
                            'sweating', 'nausea', 'shortness of breath']
        if 'chest' in text and 'pain' in text:
            if any(ind in text for ind in cardiac_indicators):
                detected.append(self.red_flags['chest_pain_cardiac'])
            # Also check high severity chest pain
            for s in symptoms:
                if 'chest' in s.name.lower() and s.severity >= 7:
                    if self.red_flags['chest_pain_cardiac'] not in detected:
                        detected.append(self.red_flags['chest_pain_cardiac'])

        # Severe hypertension
        if vitals:
            sbp = vitals.get('systolic_bp') or vitals.get('systolic')
            dbp = vitals.get('diastolic_bp') or vitals.get('diastolic')
            if sbp and dbp and sbp > 180 and dbp > 120:
                if any(kw in text for kw in ['headache', 'vision', 'chest', 'confusion']):
                    detected.append(self.red_flags['severe_hypertension'])

        # Syncope with cardiac features
        if 'faint' in text or 'passed out' in text or 'syncope' in text:
            if any(kw in text for kw in ['palpitation', 'racing', 'exercise', 'exertion']):
                detected.append(self.red_flags['syncope_cardiac'])

        # DVT signs
        if 'leg' in text and 'swell' in text:
            if 'one' in text or 'unilateral' in text or 'left' in text or 'right' in text:
                detected.append(self.red_flags['leg_swelling_asymmetric'])

        return detected

    def _check_respiratory_red_flags(
        self, symptoms: List[Symptom], text: str, vitals: Optional[Dict]
    ) -> List[RedFlag]:
        """Check respiratory red flags."""
        detected = []

        # Severe respiratory distress
        distress_keywords = ['can\'t breathe', 'gasping', 'suffocating', 'severe shortness',
                           'turning blue', 'cyanosis', 'struggling to breathe']
        if any(kw in text for kw in distress_keywords):
            detected.append(self.red_flags['severe_respiratory_distress'])

        # Also check vitals for respiratory distress
        if vitals:
            rr = vitals.get('respiratory_rate')
            spo2 = vitals.get('oxygen_saturation') or vitals.get('spo2')
            if (rr and rr > 28) or (spo2 and spo2 < 90):
                detected.append(self.red_flags['severe_respiratory_distress'])

        # Hemoptysis
        if 'blood' in text and ('cough' in text or 'sputum' in text):
            detected.append(self.red_flags['hemoptysis_significant'])

        # PE signs
        if 'chest pain' in text and 'breath' in text:
            if 'sudden' in text or 'sharp' in text:
                detected.append(self.red_flags['sudden_pleuritic_pain'])

        return detected

    def _check_gi_red_flags(
        self, symptoms: List[Symptom], text: str, vitals: Optional[Dict]
    ) -> List[RedFlag]:
        """Check GI red flags."""
        detected = []

        # GI bleeding
        gi_bleed_keywords = ['vomit blood', 'blood in vomit', 'hematemesis', 'black stool',
                           'tarry stool', 'melena', 'blood in stool', 'rectal bleeding']
        if any(kw in text for kw in gi_bleed_keywords):
            detected.append(self.red_flags['gi_bleeding_acute'])

        # Acute abdomen
        if 'abdom' in text and 'pain' in text:
            acute_signs = ['rigid', 'rebound', 'guarding', 'can\'t move', 'worst pain',
                         'tearing', 'sudden severe']
            if any(sign in text for sign in acute_signs):
                detected.append(self.red_flags['severe_abdominal_pain'])

        return detected

    def _check_infectious_red_flags(
        self, symptoms: List[Symptom], text: str, vitals: Optional[Dict]
    ) -> List[RedFlag]:
        """Check infectious disease red flags."""
        detected = []

        # Sepsis
        if 'fever' in text or (vitals and vitals.get('temperature', 0) >= 38.3):
            sepsis_signs = ['confusion', 'rapid heart', 'fast breathing', 'shaking',
                          'very sick', 'getting worse', 'low blood pressure']
            if any(sign in text for sign in sepsis_signs):
                detected.append(self.red_flags['sepsis_criteria'])
            if vitals:
                hr = vitals.get('heart_rate') or vitals.get('pulse')
                rr = vitals.get('respiratory_rate')
                if (hr and hr > 100) or (rr and rr > 22):
                    detected.append(self.red_flags['sepsis_criteria'])

        # Meningitis
        if 'headache' in text and 'fever' in text:
            if any(sign in text for sign in ['stiff neck', 'light hurts', 'photophobia', 'rash']):
                detected.append(self.red_flags['meningitis_signs'])

        return detected

    def _check_psychiatric_red_flags(
        self, symptoms: List[Symptom], text: str
    ) -> List[RedFlag]:
        """Check psychiatric red flags."""
        detected = []

        # Suicidal ideation
        suicide_keywords = ['suicid', 'kill myself', 'end my life', 'want to die',
                          'better off dead', 'no reason to live', 'self-harm', 'hurt myself']
        if any(kw in text for kw in suicide_keywords):
            detected.append(self.red_flags['suicidal_ideation'])

        # Acute psychosis
        psychosis_keywords = ['hallucin', 'hearing voices', 'seeing things', 'paranoid',
                            'people following', 'not real', 'delusional']
        if any(kw in text for kw in psychosis_keywords):
            detected.append(self.red_flags['acute_psychosis'])

        return detected

    def _check_obstetric_red_flags(
        self, symptoms: List[Symptom], text: str,
        patient_sex: Optional[str], patient_age: Optional[int]
    ) -> List[RedFlag]:
        """Check obstetric red flags."""
        detected = []

        # Only check for female patients of childbearing age
        if patient_sex and patient_sex.lower() in ['f', 'female']:
            if patient_age is None or (12 <= patient_age <= 55):
                if 'pelvic' in text and 'pain' in text:
                    if 'bleeding' in text or 'spotting' in text:
                        detected.append(self.red_flags['ectopic_pregnancy_signs'])

        return detected

    def _check_allergic_red_flags(
        self, symptoms: List[Symptom], text: str
    ) -> List[RedFlag]:
        """Check for anaphylaxis."""
        detected = []

        anaphylaxis_signs = ['hives', 'swelling', 'throat closing', 'can\'t swallow',
                           'allergic reaction', 'bee sting', 'peanut', 'epipen']
        if any(sign in text for sign in anaphylaxis_signs):
            if any(s.severity >= 7 for s in symptoms) or 'breath' in text:
                detected.append(self.red_flags['anaphylaxis'])

        return detected


class TriageEngine:
    """Main triage engine with full explainability."""

    def __init__(self):
        self.symptom_analyzer = SymptomAnalyzer()
        self.red_flag_detector = RedFlagDetector()
        self.department_router = DepartmentRouter()

    async def triage_patient(
        self,
        symptoms: List[Dict[str, Any]],
        vitals: Optional[Dict[str, Any]] = None,
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
        medical_history: Optional[List[str]] = None,
        current_medications: Optional[List[str]] = None,
        allergies: Optional[List[str]] = None,
        chief_complaint: Optional[str] = None
    ) -> TriageDecision:
        """Perform comprehensive triage assessment."""
        decision_path = []
        contributing_factors = []

        # Step 1: Parse and analyze symptoms
        decision_path.append("Analyzing reported symptoms")
        analyzed_symptoms = []
        for s in symptoms:
            if isinstance(s, dict):
                analyzed = self.symptom_analyzer.analyze_symptom(
                    s.get('description', s.get('name', '')),
                    s.get('severity')
                )
                analyzed.name = s.get('name', analyzed.name)
                if s.get('severity'):
                    analyzed.severity = s['severity']
                analyzed_symptoms.append(analyzed)

        # Step 2: Detect red flags (100% sensitivity target)
        decision_path.append("Screening for clinical red flags")
        red_flags = self.red_flag_detector.detect_red_flags(
            analyzed_symptoms,
            vitals,
            patient_age,
            patient_sex,
            medical_history,
            chief_complaint
        )

        if red_flags:
            contributing_factors.append({
                "factor": "Red flags detected",
                "impact": "critical",
                "details": [rf.name for rf in red_flags]
            })

        # Step 3: Calculate urgency score
        decision_path.append("Calculating urgency score")
        urgency_level, urgency_score = self._calculate_urgency(
            analyzed_symptoms, red_flags, vitals, patient_age, medical_history
        )

        contributing_factors.append({
            "factor": "Symptom severity",
            "impact": "high" if urgency_score > 70 else "moderate" if urgency_score > 40 else "low",
            "details": f"Average severity: {sum(s.severity for s in analyzed_symptoms) / max(len(analyzed_symptoms), 1):.1f}/10"
        })

        # Step 4: Determine body systems involved
        body_systems = list(set(
            s.body_system for s in analyzed_symptoms if s.body_system
        ))

        # Step 5: Route to appropriate department
        decision_path.append("Determining appropriate care setting")
        department, alt_departments = self.department_router.route(
            analyzed_symptoms, red_flags, body_systems, patient_age
        )

        # Step 6: Generate clinical assessment
        decision_path.append("Generating clinical assessment")
        primary_concern, differentials = self._assess_clinical_picture(
            analyzed_symptoms, red_flags, chief_complaint
        )

        # Step 7: Generate recommendations
        decision_path.append("Formulating recommendations")
        recommendations = self._generate_recommendations(
            urgency_level, red_flags, department
        )

        self_care = self._generate_self_care_advice(
            analyzed_symptoms, urgency_level
        )

        warning_signs = self._generate_warning_signs(
            analyzed_symptoms, red_flags
        )

        # Step 8: Calculate confidence
        confidence = self._calculate_confidence(
            analyzed_symptoms, red_flags, vitals
        )

        # Step 9: Generate explainability
        rationale = self._generate_rationale(
            urgency_level, red_flags, analyzed_symptoms, department
        )

        evidence = self._gather_evidence_citations(red_flags)

        # Step 10: Determine care setting and timeframe
        care_setting, timeframe = self._determine_care_setting(urgency_level)

        return TriageDecision(
            decision_id=uuid4(),
            urgency_level=urgency_level,
            urgency_score=urgency_score,
            confidence_score=confidence,
            primary_concern=primary_concern,
            differential_considerations=differentials,
            body_systems_involved=body_systems,
            red_flags_identified=red_flags,
            red_flag_count=len(red_flags),
            recommended_department=department,
            alternative_departments=alt_departments,
            timeframe=timeframe,
            care_setting=care_setting,
            recommended_actions=recommendations,
            self_care_advice=self_care,
            warning_signs_to_watch=warning_signs,
            decision_rationale=rationale,
            contributing_factors=contributing_factors,
            evidence_citations=evidence,
            decision_path=decision_path,
            disclaimer=self._get_disclaimer(),
            requires_human_review=len(red_flags) > 0 or confidence < 0.7
        )

    def _calculate_urgency(
        self,
        symptoms: List[Symptom],
        red_flags: List[RedFlag],
        vitals: Optional[Dict],
        patient_age: Optional[int],
        medical_history: Optional[List[str]]
    ) -> Tuple[UrgencyLevel, int]:
        """Calculate urgency level and score."""
        score = 0

        # Red flags are highest priority
        if red_flags:
            max_urgency = min(rf.urgency for rf in red_flags)
            if max_urgency == UrgencyLevel.EMERGENCY:
                return UrgencyLevel.EMERGENCY, 100
            elif max_urgency == UrgencyLevel.URGENT:
                score = 80

        # Symptom severity contribution (0-40 points)
        if symptoms:
            avg_severity = sum(s.severity for s in symptoms) / len(symptoms)
            max_severity = max(s.severity for s in symptoms)
            score += int((avg_severity / 10) * 20 + (max_severity / 10) * 20)

        # Vital sign abnormalities (0-20 points)
        if vitals:
            vitals_score = self._score_vitals(vitals)
            score += vitals_score

        # Age risk factor (0-10 points)
        if patient_age:
            if patient_age < 2 or patient_age > 75:
                score += 10
            elif patient_age < 5 or patient_age > 65:
                score += 5

        # Medical history risk (0-10 points)
        if medical_history:
            high_risk_conditions = ['diabetes', 'heart disease', 'copd', 'cancer',
                                   'immunocompromised', 'kidney disease']
            for condition in medical_history:
                if any(hrc in condition.lower() for hrc in high_risk_conditions):
                    score += 5
                    break

        score = min(100, score)

        # Map score to urgency level
        if score >= 85:
            return UrgencyLevel.EMERGENCY, score
        elif score >= 70:
            return UrgencyLevel.URGENT, score
        elif score >= 50:
            return UrgencyLevel.LESS_URGENT, score
        elif score >= 30:
            return UrgencyLevel.SEMI_URGENT, score
        elif score >= 15:
            return UrgencyLevel.NON_URGENT, score
        else:
            return UrgencyLevel.SELF_CARE, score

    def _score_vitals(self, vitals: Dict) -> int:
        """Score vital sign abnormalities."""
        score = 0

        # Heart rate
        hr = vitals.get('heart_rate') or vitals.get('pulse')
        if hr:
            if hr > 120 or hr < 50:
                score += 5
            elif hr > 100 or hr < 60:
                score += 2

        # Blood pressure
        sbp = vitals.get('systolic_bp') or vitals.get('systolic')
        if sbp:
            if sbp > 180 or sbp < 90:
                score += 5
            elif sbp > 160 or sbp < 100:
                score += 2

        # Oxygen saturation
        spo2 = vitals.get('oxygen_saturation') or vitals.get('spo2')
        if spo2:
            if spo2 < 90:
                score += 10
            elif spo2 < 94:
                score += 5

        # Temperature
        temp = vitals.get('temperature')
        if temp:
            if temp > 39.5 or temp < 35:
                score += 5
            elif temp > 38.5:
                score += 2

        # Respiratory rate
        rr = vitals.get('respiratory_rate')
        if rr:
            if rr > 28 or rr < 10:
                score += 5
            elif rr > 22 or rr < 12:
                score += 2

        return min(20, score)

    def _assess_clinical_picture(
        self,
        symptoms: List[Symptom],
        red_flags: List[RedFlag],
        chief_complaint: Optional[str]
    ) -> Tuple[str, List[str]]:
        """Assess primary concern and differential considerations."""
        # Primary concern is based on chief complaint and most severe symptom
        if red_flags:
            primary = f"Possible {red_flags[0].name.lower()}"
        elif chief_complaint:
            primary = f"Patient presenting with {chief_complaint}"
        elif symptoms:
            most_severe = max(symptoms, key=lambda s: s.severity)
            primary = f"Primary symptom: {most_severe.name}"
        else:
            primary = "Symptom assessment required"

        # Generate differential considerations (not diagnoses)
        differentials = []
        body_systems = set(s.body_system for s in symptoms if s.body_system)

        for system in body_systems:
            if system == BodySystem.CARDIOVASCULAR:
                differentials.append("Cardiovascular evaluation recommended")
            elif system == BodySystem.RESPIRATORY:
                differentials.append("Respiratory assessment needed")
            elif system == BodySystem.NEUROLOGICAL:
                differentials.append("Neurological workup may be indicated")
            elif system == BodySystem.GASTROINTESTINAL:
                differentials.append("GI evaluation recommended")

        return primary, differentials[:5]

    def _generate_recommendations(
        self,
        urgency: UrgencyLevel,
        red_flags: List[RedFlag],
        department: Department
    ) -> List[str]:
        """Generate recommended actions."""
        recommendations = []

        if urgency == UrgencyLevel.EMERGENCY:
            recommendations.append("Seek emergency care immediately")
            recommendations.append("Call 911 if unable to transport safely")
        elif urgency == UrgencyLevel.URGENT:
            recommendations.append(f"Visit {department.value.replace('_', ' ')} within 2-4 hours")
            recommendations.append("Do not drive if experiencing dizziness or confusion")
        elif urgency == UrgencyLevel.LESS_URGENT:
            recommendations.append(f"Schedule appointment with {department.value.replace('_', ' ')} today")
        else:
            recommendations.append("Consider scheduling a routine appointment")

        # Add red flag specific recommendations
        for rf in red_flags[:3]:
            recommendations.append(rf.action_required)

        return recommendations[:6]

    def _generate_self_care_advice(
        self,
        symptoms: List[Symptom],
        urgency: UrgencyLevel
    ) -> List[str]:
        """Generate self-care advice."""
        advice = []

        if urgency in [UrgencyLevel.EMERGENCY, UrgencyLevel.URGENT]:
            advice.append("Do not delay seeking medical care")
            advice.append("Have someone accompany you to the hospital")
            return advice

        # General advice based on symptoms
        body_systems = set(s.body_system for s in symptoms if s.body_system)

        if BodySystem.RESPIRATORY in body_systems:
            advice.append("Stay hydrated with warm fluids")
            advice.append("Use a humidifier if available")

        if BodySystem.GASTROINTESTINAL in body_systems:
            advice.append("Maintain clear fluid intake")
            advice.append("Avoid solid foods until nausea subsides")

        if BodySystem.MUSCULOSKELETAL in body_systems:
            advice.append("Apply ice to reduce swelling (20 min on, 20 min off)")
            advice.append("Rest the affected area")

        advice.append("Monitor symptoms and seek care if they worsen")
        advice.append("Keep a record of symptoms to share with your provider")

        return advice[:5]

    def _generate_warning_signs(
        self,
        symptoms: List[Symptom],
        red_flags: List[RedFlag]
    ) -> List[str]:
        """Generate warning signs to watch for."""
        warning_signs = [
            "Symptoms suddenly getting worse",
            "New symptoms developing",
            "Difficulty breathing",
            "Severe pain that doesn't improve",
            "Confusion or altered consciousness"
        ]

        # Add specific warnings based on red flags
        for rf in red_flags:
            warning_signs.append(f"Any worsening of {rf.name.lower()}")

        return warning_signs[:7]

    def _calculate_confidence(
        self,
        symptoms: List[Symptom],
        red_flags: List[RedFlag],
        vitals: Optional[Dict]
    ) -> float:
        """Calculate confidence score for the triage decision."""
        confidence = 0.5  # Base confidence

        # More symptoms analyzed = higher confidence
        if len(symptoms) >= 2:
            confidence += 0.1
        if len(symptoms) >= 4:
            confidence += 0.1

        # Vitals available = higher confidence
        if vitals:
            confidence += 0.15
            if len(vitals) >= 3:
                confidence += 0.05

        # Clear red flags = higher confidence
        if red_flags:
            confidence += 0.1

        # Symptom detail quality
        detailed_count = sum(1 for s in symptoms if s.duration_hours or s.onset)
        if detailed_count > 0:
            confidence += 0.1 * min(detailed_count / len(symptoms), 1.0)

        return min(0.95, confidence)

    def _generate_rationale(
        self,
        urgency: UrgencyLevel,
        red_flags: List[RedFlag],
        symptoms: List[Symptom],
        department: Department
    ) -> str:
        """Generate human-readable decision rationale."""
        parts = []

        if red_flags:
            parts.append(f"Critical finding(s) identified: {', '.join(rf.name for rf in red_flags)}.")

        if symptoms:
            avg_severity = sum(s.severity for s in symptoms) / len(symptoms)
            parts.append(f"Average symptom severity: {avg_severity:.1f}/10.")

        parts.append(f"Urgency classification: {urgency.value}.")
        parts.append(f"Recommended care setting: {department.value.replace('_', ' ')}.")

        if red_flags:
            parts.append(f"Rationale: {red_flags[0].rationale}")

        return ' '.join(parts)

    def _gather_evidence_citations(self, red_flags: List[RedFlag]) -> List[str]:
        """Gather evidence citations from red flags."""
        citations = set()
        for rf in red_flags:
            citations.add(rf.evidence_source)
        return list(citations)[:5]

    def _determine_care_setting(
        self, urgency: UrgencyLevel
    ) -> Tuple[str, str]:
        """Determine care setting and timeframe."""
        if urgency == UrgencyLevel.EMERGENCY:
            return "Emergency Department", "Immediate"
        elif urgency == UrgencyLevel.URGENT:
            return "Urgent Care / Emergency", "Within 2 hours"
        elif urgency == UrgencyLevel.LESS_URGENT:
            return "Urgent Care / Same-day appointment", "Within 24 hours"
        elif urgency == UrgencyLevel.SEMI_URGENT:
            return "Primary Care / Clinic", "Within 48-72 hours"
        elif urgency == UrgencyLevel.NON_URGENT:
            return "Primary Care", "Within 1 week"
        else:
            return "Home / Telehealth if needed", "As needed"

    def _get_disclaimer(self) -> str:
        """Return standard medical disclaimer."""
        return (
            "This triage assessment is intended to help prioritize care and is not a "
            "medical diagnosis. It should not replace professional medical advice, "
            "diagnosis, or treatment. If you believe you are experiencing a medical "
            "emergency, call 911 or go to the nearest emergency room immediately."
        )


class DepartmentRouter:
    """Route patients to appropriate departments."""

    def route(
        self,
        symptoms: List[Symptom],
        red_flags: List[RedFlag],
        body_systems: List[BodySystem],
        patient_age: Optional[int]
    ) -> Tuple[Department, List[Department]]:
        """Route to appropriate department."""
        alternatives = []

        # Emergency takes priority for red flags
        if red_flags:
            emergency_flags = [rf for rf in red_flags if rf.urgency == UrgencyLevel.EMERGENCY]
            if emergency_flags:
                return Department.EMERGENCY, [Department.URGENT_CARE]

        # Age-based routing
        if patient_age:
            if patient_age < 18:
                alternatives.append(Department.PEDIATRICS)
            elif patient_age > 65:
                alternatives.append(Department.GERIATRICS)

        # Body system routing
        if BodySystem.CARDIOVASCULAR in body_systems:
            return Department.CARDIOLOGY, [Department.EMERGENCY, Department.PRIMARY_CARE]

        if BodySystem.NEUROLOGICAL in body_systems:
            return Department.NEUROLOGY, [Department.EMERGENCY, Department.PRIMARY_CARE]

        if BodySystem.RESPIRATORY in body_systems:
            return Department.PULMONOLOGY, [Department.URGENT_CARE, Department.PRIMARY_CARE]

        if BodySystem.GASTROINTESTINAL in body_systems:
            return Department.GASTROENTEROLOGY, [Department.URGENT_CARE, Department.PRIMARY_CARE]

        if BodySystem.MUSCULOSKELETAL in body_systems:
            return Department.ORTHOPEDICS, [Department.URGENT_CARE, Department.PRIMARY_CARE]

        if BodySystem.PSYCHIATRIC in body_systems:
            return Department.PSYCHIATRY, [Department.EMERGENCY, Department.PRIMARY_CARE]

        if BodySystem.DERMATOLOGICAL in body_systems:
            return Department.DERMATOLOGY, [Department.URGENT_CARE, Department.PRIMARY_CARE]

        if BodySystem.OPHTHALMOLOGICAL in body_systems:
            return Department.OPHTHALMOLOGY, [Department.URGENT_CARE]

        if BodySystem.ENT in body_systems:
            return Department.ENT, [Department.URGENT_CARE, Department.PRIMARY_CARE]

        # Default to primary care
        return Department.PRIMARY_CARE, [Department.URGENT_CARE] + alternatives


# Global triage engine instance
triage_engine = TriageEngine()
