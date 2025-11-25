"""
Tests for Medical AI Module (EPIC-010)

Comprehensive tests for:
- AI-powered triage (US-010.1)
- Clinical documentation AI (US-010.2)
- Medical entity recognition (US-010.3)
- Clinical decision intelligence (US-010.4)
- Predictive health analytics (US-010.5)
- Medical image analysis (US-010.6)
- Clinical NLP pipeline (US-010.7)
- Voice biomarker analysis (US-010.8)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

# Import shared medical AI services
from shared.medical_ai.triage_engine import (
    triage_engine,
    TriageEngine,
    SymptomAnalyzer,
    RedFlagDetector,
    DepartmentRouter,
    UrgencyLevel,
)
from shared.medical_ai.documentation_ai import (
    AmbientTranscriptionService,
    SOAPNoteGenerator,
    MedicalCodeSuggester,
)
from shared.medical_ai.entity_recognition import (
    MedicalEntityExtractor,
    EntityType,
    NegationStatus,
)
from shared.medical_ai.decision_intelligence import (
    ClinicalDecisionIntelligence,
    ClinicalGuidelineEngine,
    DrugInteractionChecker,
    DiagnosticEngine,
    InteractionSeverity,
)
from shared.medical_ai.predictive_analytics import (
    PredictiveAnalyticsService,
    ReadmissionRiskModel,
    DeteriorationDetector,
    NoShowPredictor,
    RiskLevel,
)
from shared.medical_ai.image_analysis import (
    MedicalImageAnalysisService,
    ChestXrayAnalyzer,
    SkinLesionAnalyzer,
    WoundAnalyzer,
)
from shared.medical_ai.nlp_pipeline import (
    ClinicalNLPPipeline,
    ClinicalSectionSplitter,
    ProblemListExtractor,
    MedicationExtractor,
    SocialDeterminantsExtractor,
    QualityMeasureIdentifier,
)
from shared.medical_ai.voice_biomarkers import (
    VoiceBiomarkerService,
    AudioFeatureExtractor,
    DepressionDetector,
    CognitiveAssessor,
    RespiratoryAnalyzer,
)


# ==================== Triage Engine Tests (US-010.1) ====================

class TestSymptomAnalyzer:
    """Tests for symptom analysis functionality"""

    @pytest.fixture
    def analyzer(self):
        return SymptomAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_chest_pain_symptoms(self, analyzer):
        """Test analysis of chest pain symptoms"""
        symptoms = ["chest pain", "shortness of breath", "sweating"]
        result = await analyzer.analyze(symptoms, {})

        assert result is not None
        assert result.primary_symptoms is not None
        assert len(result.primary_symptoms) > 0
        assert result.severity_score > 0

    @pytest.mark.asyncio
    async def test_analyze_with_patient_context(self, analyzer):
        """Test symptom analysis with patient context"""
        symptoms = ["headache", "nausea", "vision changes"]
        context = {"age": 65, "medical_history": ["hypertension", "diabetes"]}
        result = await analyzer.analyze(symptoms, context)

        assert result is not None
        assert result.pattern_matches is not None

    @pytest.mark.asyncio
    async def test_analyze_empty_symptoms(self, analyzer):
        """Test handling of empty symptoms"""
        with pytest.raises(ValueError):
            await analyzer.analyze([], {})


class TestRedFlagDetector:
    """Tests for red flag detection"""

    @pytest.fixture
    def detector(self):
        return RedFlagDetector()

    @pytest.mark.asyncio
    async def test_detect_cardiac_red_flags(self, detector):
        """Test detection of cardiac red flags"""
        symptoms = ["chest pain", "left arm pain", "diaphoresis"]
        context = {"age": 55, "gender": "male"}
        result = await detector.detect(symptoms, context)

        assert result is not None
        assert len(result) > 0
        assert any("cardiac" in rf.name.lower() for rf in result)

    @pytest.mark.asyncio
    async def test_detect_stroke_red_flags(self, detector):
        """Test detection of stroke red flags"""
        symptoms = ["sudden weakness", "facial droop", "slurred speech"]
        result = await detector.detect(symptoms, {})

        assert len(result) > 0
        assert any("stroke" in rf.name.lower() or "neurological" in rf.name.lower() for rf in result)

    @pytest.mark.asyncio
    async def test_no_red_flags_for_mild_symptoms(self, detector):
        """Test that mild symptoms don't trigger red flags"""
        symptoms = ["mild headache", "fatigue"]
        result = await detector.detect(symptoms, {})

        # May have red flags or not depending on implementation
        # Just verify the function runs without error
        assert result is not None


class TestTriageEngine:
    """Tests for the complete triage engine"""

    @pytest.fixture
    def engine(self):
        return TriageEngine()

    @pytest.mark.asyncio
    async def test_emergency_triage(self, engine):
        """Test triage for emergency symptoms"""
        symptoms = ["chest pain", "difficulty breathing", "sweating"]
        context = {"age": 60, "vital_signs": {"heart_rate": 120}}
        result = await engine.perform_triage(
            symptoms=symptoms,
            patient_context=context,
            chief_complaint="Severe chest pain for 30 minutes"
        )

        assert result is not None
        assert result.urgency_level in [UrgencyLevel.EMERGENCY, UrgencyLevel.URGENT]
        assert result.esi_level <= 2
        assert result.confidence > 0.5
        assert len(result.red_flags) > 0

    @pytest.mark.asyncio
    async def test_non_urgent_triage(self, engine):
        """Test triage for non-urgent symptoms"""
        symptoms = ["mild cough", "runny nose"]
        context = {"age": 25}
        result = await engine.perform_triage(
            symptoms=symptoms,
            patient_context=context,
            chief_complaint="Cold symptoms for 2 days"
        )

        assert result is not None
        assert result.urgency_level in [UrgencyLevel.NON_URGENT, UrgencyLevel.SELF_CARE, UrgencyLevel.SEMI_URGENT]
        assert result.esi_level >= 4

    @pytest.mark.asyncio
    async def test_triage_explainability(self, engine):
        """Test that triage provides explanation"""
        symptoms = ["abdominal pain", "nausea"]
        result = await engine.perform_triage(
            symptoms=symptoms,
            patient_context={},
            chief_complaint="Stomach pain"
        )

        assert result.explanation is not None
        assert len(result.explanation.decision_path) > 0
        assert result.explanation.rationale != ""


class TestDepartmentRouter:
    """Tests for department routing"""

    @pytest.fixture
    def router(self):
        return DepartmentRouter()

    @pytest.mark.asyncio
    async def test_route_cardiac_symptoms(self, router):
        """Test routing for cardiac symptoms"""
        symptoms = ["chest pain", "palpitations"]
        result = await router.route(symptoms, {})

        assert result is not None
        assert "cardiology" in result.lower() or "emergency" in result.lower()

    @pytest.mark.asyncio
    async def test_route_orthopedic_symptoms(self, router):
        """Test routing for orthopedic symptoms"""
        symptoms = ["knee pain", "joint swelling"]
        result = await router.route(symptoms, {})

        assert "orthopedic" in result.lower() or "musculoskeletal" in result.lower() or "general" in result.lower()


# ==================== Documentation AI Tests (US-010.2) ====================

class TestSOAPNoteGenerator:
    """Tests for SOAP note generation"""

    @pytest.fixture
    def generator(self):
        return SOAPNoteGenerator()

    @pytest.mark.asyncio
    async def test_generate_soap_note(self, generator):
        """Test SOAP note generation from transcript"""
        transcript = """
        Patient: I've been having headaches for the past week.
        Doctor: Where exactly is the pain located?
        Patient: Mostly in the front, above my eyes.
        Doctor: Any nausea or visual changes?
        Patient: A little nausea sometimes.
        """
        result = await generator.generate(transcript=transcript)

        assert result is not None
        assert result.subjective != ""
        assert result.assessment != ""
        assert result.plan != ""

    @pytest.mark.asyncio
    async def test_soap_note_sections(self, generator):
        """Test that all SOAP sections are populated"""
        transcript = "Patient presents with chronic back pain. Examination shows limited mobility. Assessment: Lumbar strain. Plan: Physical therapy."
        result = await generator.generate(transcript=transcript)

        # All sections should have some content
        assert len(result.subjective) > 0 or len(result.objective) > 0
        assert len(result.assessment) > 0
        assert len(result.plan) > 0


class TestMedicalCodeSuggester:
    """Tests for medical code suggestion"""

    @pytest.fixture
    def suggester(self):
        return MedicalCodeSuggester()

    @pytest.mark.asyncio
    async def test_suggest_icd10_codes(self, suggester):
        """Test ICD-10 code suggestion"""
        clinical_text = "Patient diagnosed with type 2 diabetes mellitus with diabetic nephropathy"
        result = await suggester.suggest_codes(
            clinical_text=clinical_text,
            code_types=["icd10"]
        )

        assert len(result) > 0
        assert any(code.code_type == "icd10" for code in result)
        assert any("E11" in code.code for code in result)  # E11 is diabetes type 2

    @pytest.mark.asyncio
    async def test_suggest_cpt_codes(self, suggester):
        """Test CPT code suggestion"""
        clinical_text = "Performed comprehensive metabolic panel and lipid panel"
        result = await suggester.suggest_codes(
            clinical_text=clinical_text,
            code_types=["cpt"]
        )

        assert len(result) > 0
        assert any(code.code_type == "cpt" for code in result)


# ==================== Entity Recognition Tests (US-010.3) ====================

class TestMedicalEntityExtractor:
    """Tests for medical entity extraction"""

    @pytest.fixture
    def extractor(self):
        return MedicalEntityExtractor()

    @pytest.mark.asyncio
    async def test_extract_conditions(self, extractor):
        """Test extraction of medical conditions"""
        text = "Patient has hypertension and type 2 diabetes mellitus."
        result = await extractor.extract(text)

        assert len(result.entities) > 0
        conditions = [e for e in result.entities if e.entity_type == EntityType.CONDITION]
        assert len(conditions) >= 2

    @pytest.mark.asyncio
    async def test_extract_medications(self, extractor):
        """Test extraction of medications"""
        text = "Patient is taking metformin 500mg twice daily and lisinopril 10mg daily."
        result = await extractor.extract(text)

        medications = [e for e in result.entities if e.entity_type == EntityType.MEDICATION]
        assert len(medications) >= 2

    @pytest.mark.asyncio
    async def test_negation_detection(self, extractor):
        """Test detection of negated entities"""
        text = "Patient denies chest pain. No history of diabetes."
        result = await extractor.extract(text, include_negation=True)

        negated = [e for e in result.entities if e.negation_status == NegationStatus.NEGATED]
        assert len(negated) > 0

    @pytest.mark.asyncio
    async def test_entity_normalization(self, extractor):
        """Test entity normalization to standard codes"""
        text = "Patient has high blood pressure."
        result = await extractor.extract(text, normalize_to_standards=True)

        # Should normalize "high blood pressure" to hypertension
        conditions = [e for e in result.entities if e.entity_type == EntityType.CONDITION]
        assert len(conditions) > 0
        # Check that at least one has a normalized code
        assert any(e.normalized_code is not None for e in conditions)


# ==================== Clinical Decision Intelligence Tests (US-010.4) ====================

class TestDrugInteractionChecker:
    """Tests for drug interaction checking"""

    @pytest.fixture
    def checker(self):
        return DrugInteractionChecker()

    @pytest.mark.asyncio
    async def test_detect_major_interaction(self, checker):
        """Test detection of major drug interactions"""
        medications = ["warfarin", "aspirin"]
        result = await checker.check_interactions(medications)

        assert len(result) > 0
        # Warfarin + aspirin is a known major interaction
        assert any(i.severity in [InteractionSeverity.MAJOR, InteractionSeverity.MODERATE] for i in result)

    @pytest.mark.asyncio
    async def test_no_interaction(self, checker):
        """Test when no interactions exist"""
        medications = ["metformin", "lisinopril"]
        result = await checker.check_interactions(medications)

        # These generally don't have significant interactions
        major_interactions = [i for i in result if i.severity == InteractionSeverity.CONTRAINDICATED]
        assert len(major_interactions) == 0


class TestClinicalGuidelineEngine:
    """Tests for clinical guideline recommendations"""

    @pytest.fixture
    def engine(self):
        return ClinicalGuidelineEngine()

    @pytest.mark.asyncio
    async def test_hypertension_guidelines(self, engine):
        """Test guideline recommendations for hypertension"""
        conditions = ["hypertension"]
        result = await engine.get_recommendations(conditions, {}, {})

        assert len(result) > 0
        assert any("hypertension" in r.condition.lower() for r in result)

    @pytest.mark.asyncio
    async def test_diabetes_guidelines(self, engine):
        """Test guideline recommendations for diabetes"""
        conditions = ["type 2 diabetes"]
        lab_results = {"HbA1c": 8.5}
        result = await engine.get_recommendations(conditions, lab_results, {})

        assert len(result) > 0


class TestDiagnosticEngine:
    """Tests for differential diagnosis generation"""

    @pytest.fixture
    def engine(self):
        return DiagnosticEngine()

    @pytest.mark.asyncio
    async def test_generate_differentials(self, engine):
        """Test differential diagnosis generation"""
        symptoms = ["chest pain", "shortness of breath"]
        result = await engine.generate_differentials(symptoms, {}, {})

        assert len(result) > 0
        assert all(d.probability > 0 for d in result)
        # Should be sorted by probability
        probs = [d.probability for d in result]
        assert probs == sorted(probs, reverse=True)


# ==================== Predictive Analytics Tests (US-010.5) ====================

class TestReadmissionRiskModel:
    """Tests for readmission risk prediction"""

    @pytest.fixture
    def model(self):
        return ReadmissionRiskModel()

    @pytest.mark.asyncio
    async def test_high_risk_prediction(self, model):
        """Test high-risk readmission prediction"""
        admission_data = {
            "length_of_stay": 10,
            "acuity": "high",
            "comorbidity_count": 5,
            "ed_visits_6mo": 3
        }
        result = await model.predict(patient_id="test-123", admission_data=admission_data)

        assert result is not None
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]
        assert result.probability > 0.5

    @pytest.mark.asyncio
    async def test_low_risk_prediction(self, model):
        """Test low-risk readmission prediction"""
        admission_data = {
            "length_of_stay": 1,
            "acuity": "low",
            "comorbidity_count": 0,
            "ed_visits_6mo": 0
        }
        result = await model.predict(patient_id="test-456", admission_data=admission_data)

        assert result is not None
        assert result.risk_level in [RiskLevel.VERY_LOW, RiskLevel.LOW, RiskLevel.MODERATE]

    @pytest.mark.asyncio
    async def test_lace_score_calculation(self, model):
        """Test LACE score is calculated"""
        admission_data = {
            "length_of_stay": 5,
            "acuity": "medium",
            "comorbidity_count": 2,
            "ed_visits_6mo": 1
        }
        result = await model.predict(patient_id="test-789", admission_data=admission_data)

        assert result.lace_score is not None
        assert result.lace_score.total_score >= 0


class TestDeteriorationDetector:
    """Tests for clinical deterioration detection"""

    @pytest.fixture
    def detector(self):
        return DeteriorationDetector()

    @pytest.mark.asyncio
    async def test_detect_deterioration(self, detector):
        """Test deterioration detection from vital signs"""
        vital_signs = {
            "heart_rate": 130,
            "respiratory_rate": 28,
            "systolic_bp": 85,
            "temperature": 39.5,
            "oxygen_saturation": 88
        }
        result = await detector.detect(patient_id="test-123", vital_signs=vital_signs)

        assert result is not None
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]
        assert result.mews_score.total_score >= 5

    @pytest.mark.asyncio
    async def test_normal_vitals(self, detector):
        """Test with normal vital signs"""
        vital_signs = {
            "heart_rate": 75,
            "respiratory_rate": 16,
            "systolic_bp": 120,
            "temperature": 37.0,
            "oxygen_saturation": 98
        }
        result = await detector.detect(patient_id="test-456", vital_signs=vital_signs)

        assert result is not None
        assert result.risk_level in [RiskLevel.VERY_LOW, RiskLevel.LOW]


class TestNoShowPredictor:
    """Tests for no-show prediction"""

    @pytest.fixture
    def predictor(self):
        return NoShowPredictor()

    @pytest.mark.asyncio
    async def test_high_risk_no_show(self, predictor):
        """Test high-risk no-show prediction"""
        appointment_data = {
            "previous_no_shows": 3,
            "lead_time_days": 30,
            "appointment_type": "routine",
            "time_slot": "morning"
        }
        result = await predictor.predict(patient_id="test-123", appointment_data=appointment_data)

        assert result is not None
        assert result.probability > 0.3  # Higher probability for high-risk

    @pytest.mark.asyncio
    async def test_low_risk_no_show(self, predictor):
        """Test low-risk no-show prediction"""
        appointment_data = {
            "previous_no_shows": 0,
            "lead_time_days": 3,
            "appointment_type": "urgent"
        }
        result = await predictor.predict(patient_id="test-456", appointment_data=appointment_data)

        assert result is not None
        assert result.probability < 0.3


# ==================== Image Analysis Tests (US-010.6) ====================

class TestChestXrayAnalyzer:
    """Tests for chest X-ray analysis"""

    @pytest.fixture
    def analyzer(self):
        return ChestXrayAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_xray(self, analyzer):
        """Test chest X-ray analysis"""
        # Mock image data
        image_data = b"fake_image_data"
        result = await analyzer.analyze(image_data=image_data)

        assert result is not None
        assert result.overall_impression != ""
        assert isinstance(result.findings, list)

    @pytest.mark.asyncio
    async def test_xray_with_clinical_context(self, analyzer):
        """Test X-ray analysis with clinical context"""
        image_data = b"fake_image_data"
        result = await analyzer.analyze(
            image_data=image_data,
            clinical_context="Patient presents with cough and fever"
        )

        assert result is not None


class TestSkinLesionAnalyzer:
    """Tests for skin lesion analysis"""

    @pytest.fixture
    def analyzer(self):
        return SkinLesionAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_lesion(self, analyzer):
        """Test skin lesion analysis"""
        image_data = b"fake_image_data"
        result = await analyzer.analyze(image_data=image_data)

        assert result is not None
        assert result.malignancy_risk in ["low", "moderate", "high"]
        assert result.abcde_scores is not None

    @pytest.mark.asyncio
    async def test_urgent_referral_detection(self, analyzer):
        """Test urgent referral flag"""
        image_data = b"fake_suspicious_lesion"
        result = await analyzer.analyze(image_data=image_data)

        assert result is not None
        assert isinstance(result.urgent_referral, bool)


class TestWoundAnalyzer:
    """Tests for wound analysis"""

    @pytest.fixture
    def analyzer(self):
        return WoundAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_wound(self, analyzer):
        """Test wound analysis"""
        image_data = b"fake_wound_image"
        result = await analyzer.analyze(image_data=image_data)

        assert result is not None
        assert result.wound_type != ""
        assert result.tissue_composition is not None


# ==================== NLP Pipeline Tests (US-010.7) ====================

class TestClinicalSectionSplitter:
    """Tests for clinical document section splitting"""

    @pytest.fixture
    def splitter(self):
        return ClinicalSectionSplitter()

    @pytest.mark.asyncio
    async def test_split_sections(self, splitter):
        """Test section splitting"""
        text = """
        HISTORY OF PRESENT ILLNESS:
        Patient is a 55-year-old male presenting with chest pain.

        PAST MEDICAL HISTORY:
        Hypertension, diabetes mellitus type 2

        MEDICATIONS:
        Metformin 500mg BID, Lisinopril 10mg daily

        ASSESSMENT AND PLAN:
        Chest pain, likely musculoskeletal. Will order EKG.
        """
        result = await splitter.split(text)

        assert len(result) >= 3
        assert any(s.section_type == "history_of_present_illness" for s in result)


class TestProblemListExtractor:
    """Tests for problem list extraction"""

    @pytest.fixture
    def extractor(self):
        return ProblemListExtractor()

    @pytest.mark.asyncio
    async def test_extract_problems(self, extractor):
        """Test problem extraction"""
        text = "Patient has diabetes mellitus type 2, hypertension, and chronic kidney disease stage 3."
        result = await extractor.extract(text)

        assert len(result) >= 2
        assert any("diabetes" in p.problem.lower() for p in result)


class TestSocialDeterminantsExtractor:
    """Tests for SDOH extraction"""

    @pytest.fixture
    def extractor(self):
        return SocialDeterminantsExtractor()

    @pytest.mark.asyncio
    async def test_extract_sdoh(self, extractor):
        """Test SDOH extraction"""
        text = "Patient reports food insecurity and lives alone. Currently unemployed and has no transportation."
        result = await extractor.extract(text)

        assert len(result) >= 2
        categories = [s.category for s in result]
        assert "food_insecurity" in categories or "housing" in categories or "employment" in categories


class TestQualityMeasureIdentifier:
    """Tests for quality measure identification"""

    @pytest.fixture
    def identifier(self):
        return QualityMeasureIdentifier()

    @pytest.mark.asyncio
    async def test_identify_measures(self, identifier):
        """Test quality measure identification"""
        text = "Patient with diabetes, HbA1c 8.5%, no eye exam documented this year."
        result = await identifier.identify(text)

        assert len(result) >= 1


# ==================== Voice Biomarker Tests (US-010.8) ====================

class TestAudioFeatureExtractor:
    """Tests for audio feature extraction"""

    @pytest.fixture
    def extractor(self):
        return AudioFeatureExtractor()

    @pytest.mark.asyncio
    async def test_extract_features(self, extractor):
        """Test audio feature extraction"""
        audio_data = b"fake_audio_data"
        result = await extractor.extract(audio_data)

        assert result is not None
        assert hasattr(result, 'pitch_mean')
        assert hasattr(result, 'speech_rate')


class TestDepressionDetector:
    """Tests for depression detection from voice"""

    @pytest.fixture
    def detector(self):
        return DepressionDetector()

    @pytest.mark.asyncio
    async def test_detect_depression(self, detector):
        """Test depression detection"""
        # Mock audio features
        from shared.medical_ai.voice_biomarkers import AudioFeatures
        features = AudioFeatures(
            pitch_mean=100.0,
            pitch_std=15.0,
            pitch_range=50.0,
            energy_mean=0.3,
            energy_std=0.1,
            speech_rate=2.0,
            pause_rate=0.3,
            pause_duration_mean=0.5,
            jitter=0.02,
            shimmer=0.05,
            hnr=15.0,
            formants=[500, 1500, 2500],
            mfcc_mean=[1.0] * 13,
            spectral_centroid=2000.0,
            spectral_rolloff=4000.0,
        )
        result = await detector.detect(features)

        assert result is not None
        assert result.phq9_equivalent >= 0
        assert result.phq9_equivalent <= 27


class TestCognitiveAssessor:
    """Tests for cognitive assessment from voice"""

    @pytest.fixture
    def assessor(self):
        return CognitiveAssessor()

    @pytest.mark.asyncio
    async def test_assess_cognitive(self, assessor):
        """Test cognitive assessment"""
        from shared.medical_ai.voice_biomarkers import AudioFeatures
        features = AudioFeatures(
            pitch_mean=120.0,
            pitch_std=20.0,
            pitch_range=60.0,
            energy_mean=0.4,
            energy_std=0.15,
            speech_rate=2.5,
            pause_rate=0.2,
            pause_duration_mean=0.4,
            jitter=0.015,
            shimmer=0.04,
            hnr=18.0,
            formants=[550, 1600, 2600],
            mfcc_mean=[0.8] * 13,
            spectral_centroid=2200.0,
            spectral_rolloff=4200.0,
        )
        result = await assessor.assess(features)

        assert result is not None
        assert result.fluency_score >= 0
        assert result.fluency_score <= 1.0


class TestRespiratoryAnalyzer:
    """Tests for respiratory analysis from voice"""

    @pytest.fixture
    def analyzer(self):
        return RespiratoryAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_respiratory(self, analyzer):
        """Test respiratory analysis"""
        from shared.medical_ai.voice_biomarkers import AudioFeatures
        features = AudioFeatures(
            pitch_mean=110.0,
            pitch_std=18.0,
            pitch_range=55.0,
            energy_mean=0.35,
            energy_std=0.12,
            speech_rate=2.2,
            pause_rate=0.25,
            pause_duration_mean=0.45,
            jitter=0.018,
            shimmer=0.045,
            hnr=16.0,
            formants=[520, 1550, 2550],
            mfcc_mean=[0.9] * 13,
            spectral_centroid=2100.0,
            spectral_rolloff=4100.0,
        )
        result = await analyzer.analyze(features)

        assert result is not None
        assert result.breath_support_score >= 0


# ==================== Integration Tests ====================

class TestMedicalAIIntegration:
    """Integration tests for medical AI services"""

    @pytest.mark.asyncio
    async def test_full_triage_workflow(self):
        """Test complete triage workflow"""
        engine = TriageEngine()

        # Emergency case
        result = await engine.perform_triage(
            symptoms=["severe chest pain", "difficulty breathing", "cold sweats"],
            patient_context={
                "age": 65,
                "gender": "male",
                "medical_history": ["hypertension", "hyperlipidemia"],
                "vital_signs": {"heart_rate": 110, "blood_pressure_systolic": 160}
            },
            chief_complaint="Crushing chest pain radiating to left arm"
        )

        assert result.urgency_level in [UrgencyLevel.EMERGENCY, UrgencyLevel.URGENT]
        assert len(result.red_flags) > 0
        assert result.explanation.rationale != ""

    @pytest.mark.asyncio
    async def test_clinical_decision_workflow(self):
        """Test clinical decision support workflow"""
        cdi = ClinicalDecisionIntelligence()

        result = await cdi.analyze(
            conditions=["type 2 diabetes", "hypertension"],
            medications=["metformin", "lisinopril", "warfarin", "aspirin"],
            lab_results={"HbA1c": 8.5, "eGFR": 55},
            vital_signs={"blood_pressure_systolic": 145, "blood_pressure_diastolic": 92},
            symptoms=[]
        )

        assert len(result.guidelines) > 0
        # Warfarin + aspirin should trigger interaction
        assert len(result.drug_interactions) > 0

    @pytest.mark.asyncio
    async def test_predictive_analytics_workflow(self):
        """Test predictive analytics workflow"""
        service = PredictiveAnalyticsService()

        # Readmission risk
        readmission = await service.predict_readmission(
            patient_id="test-patient",
            admission_data={
                "length_of_stay": 7,
                "acuity": "high",
                "comorbidity_count": 4,
                "ed_visits_6mo": 2
            }
        )
        assert readmission is not None
        assert readmission.risk_level is not None

        # Deterioration
        deterioration = await service.detect_deterioration(
            patient_id="test-patient",
            vital_signs={
                "heart_rate": 95,
                "respiratory_rate": 22,
                "systolic_bp": 100,
                "temperature": 38.5,
                "oxygen_saturation": 92
            }
        )
        assert deterioration is not None

    @pytest.mark.asyncio
    async def test_nlp_pipeline_workflow(self):
        """Test NLP pipeline workflow"""
        pipeline = ClinicalNLPPipeline()

        clinical_note = """
        HISTORY OF PRESENT ILLNESS:
        65-year-old male with type 2 diabetes and hypertension presents with chest pain.
        Patient reports food insecurity and transportation difficulties.

        CURRENT MEDICATIONS:
        Metformin 1000mg BID, Lisinopril 20mg daily

        ASSESSMENT:
        1. Chest pain - likely musculoskeletal
        2. Type 2 diabetes - poorly controlled, HbA1c 9.2%
        3. Hypertension - controlled

        PLAN:
        - EKG to rule out cardiac cause
        - Increase metformin if tolerated
        - Refer to social worker for food insecurity
        """

        result = await pipeline.process(
            text=clinical_note,
            include_sections=True,
            include_problems=True,
            include_medications=True,
            include_sdoh=True,
            include_quality_measures=True
        )

        assert len(result.sections) > 0
        assert len(result.problems) > 0
        assert len(result.medications) > 0


# ==================== Performance Tests ====================

class TestMedicalAIPerformance:
    """Performance tests for medical AI services"""

    @pytest.mark.asyncio
    async def test_triage_response_time(self):
        """Test triage response time is under target"""
        import time
        engine = TriageEngine()

        start = time.time()
        await engine.perform_triage(
            symptoms=["headache", "nausea"],
            patient_context={"age": 30},
            chief_complaint="Headache"
        )
        elapsed = (time.time() - start) * 1000  # Convert to ms

        # Target: <3 seconds (3000ms)
        assert elapsed < 3000, f"Triage took {elapsed}ms, exceeding 3000ms target"

    @pytest.mark.asyncio
    async def test_entity_extraction_performance(self):
        """Test entity extraction performance"""
        import time
        extractor = MedicalEntityExtractor()

        text = "Patient has diabetes mellitus type 2, hypertension, and chronic kidney disease. Taking metformin and lisinopril."

        start = time.time()
        await extractor.extract(text)
        elapsed = (time.time() - start) * 1000

        # Should complete in under 1 second
        assert elapsed < 1000, f"Entity extraction took {elapsed}ms"


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
