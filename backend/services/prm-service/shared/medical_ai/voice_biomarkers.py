"""
Voice Biomarker Analysis Service

EPIC-010: Medical AI Capabilities
US-010.8: Voice Biomarker Analysis

Voice-based health assessment:
- Depression screening from voice
- Cognitive assessment
- Respiratory condition detection
- Parkinson's disease detection
- Longitudinal tracking
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4, UUID
import math


class VoiceBiomarkerType(str, Enum):
    """Types of voice biomarkers."""
    DEPRESSION = "depression"
    ANXIETY = "anxiety"
    COGNITIVE_DECLINE = "cognitive_decline"
    PARKINSONS = "parkinsons"
    RESPIRATORY = "respiratory"
    FATIGUE = "fatigue"
    STRESS = "stress"


class AssessmentSeverity(str, Enum):
    """Assessment severity levels."""
    NORMAL = "normal"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


@dataclass
class AudioFeatures:
    """Extracted audio features."""
    # Prosody features
    pitch_mean: float
    pitch_std: float
    pitch_range: float

    # Timing features
    speech_rate: float  # syllables per second
    pause_frequency: float
    pause_duration_mean: float
    articulation_rate: float

    # Energy features
    energy_mean: float
    energy_std: float

    # Spectral features
    spectral_centroid: float
    spectral_bandwidth: float
    mfcc_features: List[float]

    # Voice quality
    jitter: float
    shimmer: float
    hnr: float  # Harmonic-to-noise ratio

    # Fluency
    filled_pause_count: int  # "um", "uh"
    word_finding_pauses: int
    repetitions: int


@dataclass
class BiomarkerScore:
    """Individual biomarker assessment score."""
    biomarker_type: VoiceBiomarkerType
    score: float  # 0-100
    severity: AssessmentSeverity
    confidence: float
    contributing_features: List[str]
    interpretation: str


@dataclass
class DepressionAssessment:
    """Depression screening from voice analysis."""
    assessment_id: UUID
    phq9_equivalent_score: int  # 0-27
    severity: AssessmentSeverity
    confidence: float

    # Contributing factors
    prosody_score: float
    energy_score: float
    speech_rate_score: float

    # Specific indicators
    indicators: List[str]
    recommendations: List[str]

    # Comparison
    change_from_baseline: Optional[float]

    created_at: datetime


@dataclass
class CognitiveAssessment:
    """Cognitive assessment from voice analysis."""
    assessment_id: UUID
    cognitive_score: float  # 0-100
    severity: AssessmentSeverity
    confidence: float

    # Domains assessed
    fluency_score: float
    word_finding_score: float
    coherence_score: float
    memory_indicators: float

    # MCI risk
    mci_risk_score: float
    dementia_risk_score: float

    # Specific findings
    findings: List[str]
    recommendations: List[str]

    created_at: datetime


@dataclass
class RespiratoryAssessment:
    """Respiratory health assessment from voice."""
    assessment_id: UUID
    respiratory_health_score: float  # 0-100
    severity: AssessmentSeverity
    confidence: float

    # Components
    breath_support_score: float
    cough_detected: bool
    wheeze_detected: bool
    stridor_detected: bool

    # Specific findings
    breathing_pattern: str
    findings: List[str]
    recommendations: List[str]

    created_at: datetime


@dataclass
class VoiceBiomarkerResult:
    """Complete voice biomarker analysis result."""
    result_id: UUID
    recording_id: str
    recording_duration_seconds: float

    # Features
    audio_features: AudioFeatures

    # Assessments
    biomarker_scores: List[BiomarkerScore]
    depression_assessment: Optional[DepressionAssessment]
    cognitive_assessment: Optional[CognitiveAssessment]
    respiratory_assessment: Optional[RespiratoryAssessment]

    # Overall
    overall_health_indicator: float  # 0-100
    priority_concerns: List[str]
    recommendations: List[str]

    # Longitudinal
    baseline_comparison: Optional[Dict[str, float]]
    trend_direction: Optional[str]  # improving, stable, declining

    # Quality
    audio_quality_score: float
    is_valid_sample: bool

    # Metadata
    model_version: str
    processing_time_ms: float
    created_at: datetime


class AudioFeatureExtractor:
    """Extract audio features from voice recordings."""

    async def extract_features(
        self,
        audio_data: bytes,
        sample_rate: int = 16000
    ) -> AudioFeatures:
        """
        Extract acoustic features from audio.

        In production, this would use:
        - librosa for audio processing
        - praat-parselmouth for voice quality
        - Trained models for specific biomarkers
        """
        # Simulated feature extraction
        # In production, would process actual audio

        return AudioFeatures(
            # Prosody (simulated values within typical ranges)
            pitch_mean=180.0,  # Hz, typical male ~120Hz, female ~210Hz
            pitch_std=30.0,
            pitch_range=100.0,

            # Timing
            speech_rate=4.5,  # syllables/second (normal: 4-6)
            pause_frequency=0.3,  # pauses per second
            pause_duration_mean=0.4,  # seconds
            articulation_rate=5.0,

            # Energy
            energy_mean=0.1,
            energy_std=0.05,

            # Spectral
            spectral_centroid=2000.0,
            spectral_bandwidth=1500.0,
            mfcc_features=[1.0] * 13,  # 13 MFCC coefficients

            # Voice quality
            jitter=0.02,  # Normal < 0.02
            shimmer=0.03,  # Normal < 0.03
            hnr=20.0,  # Higher is better, normal > 20

            # Fluency
            filled_pause_count=3,
            word_finding_pauses=1,
            repetitions=0
        )


class DepressionDetector:
    """Detect depression indicators from voice."""

    # Reference ranges for depression indicators
    DEPRESSION_INDICATORS = {
        'low_pitch_variation': {
            'threshold': 20.0,  # pitch_std below this
            'weight': 0.25,
            'description': 'Reduced pitch variation (monotone speech)'
        },
        'slow_speech_rate': {
            'threshold': 3.5,  # syllables/second
            'weight': 0.2,
            'description': 'Slower than normal speech rate'
        },
        'low_energy': {
            'threshold': 0.05,
            'weight': 0.2,
            'description': 'Reduced vocal energy'
        },
        'long_pauses': {
            'threshold': 0.6,  # seconds
            'weight': 0.15,
            'description': 'Prolonged pauses during speech'
        },
        'high_pause_frequency': {
            'threshold': 0.5,
            'weight': 0.1,
            'description': 'Frequent pauses in speech'
        },
        'low_hnr': {
            'threshold': 15.0,
            'weight': 0.1,
            'description': 'Reduced voice clarity'
        }
    }

    async def assess(
        self,
        features: AudioFeatures,
        baseline: Optional[AudioFeatures] = None
    ) -> DepressionAssessment:
        """Assess depression indicators from voice features."""

        indicators = []
        total_weight = 0
        weighted_score = 0

        # Check each indicator
        if features.pitch_std < self.DEPRESSION_INDICATORS['low_pitch_variation']['threshold']:
            indicators.append(self.DEPRESSION_INDICATORS['low_pitch_variation']['description'])
            weight = self.DEPRESSION_INDICATORS['low_pitch_variation']['weight']
            weighted_score += weight * (1 - features.pitch_std / 30.0)
            total_weight += weight

        if features.speech_rate < self.DEPRESSION_INDICATORS['slow_speech_rate']['threshold']:
            indicators.append(self.DEPRESSION_INDICATORS['slow_speech_rate']['description'])
            weight = self.DEPRESSION_INDICATORS['slow_speech_rate']['weight']
            weighted_score += weight * (1 - features.speech_rate / 4.5)
            total_weight += weight

        if features.energy_mean < self.DEPRESSION_INDICATORS['low_energy']['threshold']:
            indicators.append(self.DEPRESSION_INDICATORS['low_energy']['description'])
            weight = self.DEPRESSION_INDICATORS['low_energy']['weight']
            weighted_score += weight
            total_weight += weight

        if features.pause_duration_mean > self.DEPRESSION_INDICATORS['long_pauses']['threshold']:
            indicators.append(self.DEPRESSION_INDICATORS['long_pauses']['description'])
            weight = self.DEPRESSION_INDICATORS['long_pauses']['weight']
            weighted_score += weight * min(features.pause_duration_mean / 1.0, 1.0)
            total_weight += weight

        if features.hnr < self.DEPRESSION_INDICATORS['low_hnr']['threshold']:
            indicators.append(self.DEPRESSION_INDICATORS['low_hnr']['description'])
            weight = self.DEPRESSION_INDICATORS['low_hnr']['weight']
            weighted_score += weight
            total_weight += weight

        # Calculate scores
        depression_score = (weighted_score / max(total_weight, 0.1)) if total_weight > 0 else 0

        # Convert to PHQ-9 equivalent (0-27)
        phq9_equivalent = int(depression_score * 27)

        # Determine severity
        if phq9_equivalent >= 20:
            severity = AssessmentSeverity.SEVERE
        elif phq9_equivalent >= 15:
            severity = AssessmentSeverity.MODERATE
        elif phq9_equivalent >= 10:
            severity = AssessmentSeverity.MILD
        else:
            severity = AssessmentSeverity.NORMAL

        # Calculate component scores
        prosody_score = 1 - (features.pitch_std / 50.0) if features.pitch_std < 30 else 0.5
        energy_score = 1 - (features.energy_mean / 0.2) if features.energy_mean < 0.1 else 0.5
        speech_rate_score = 1 - (features.speech_rate / 6.0) if features.speech_rate < 4.0 else 0.5

        # Generate recommendations
        recommendations = self._generate_recommendations(severity, indicators)

        # Compare to baseline if available
        change_from_baseline = None
        if baseline:
            baseline_assessment = await self._quick_assess(baseline)
            change_from_baseline = depression_score - baseline_assessment

        return DepressionAssessment(
            assessment_id=uuid4(),
            phq9_equivalent_score=phq9_equivalent,
            severity=severity,
            confidence=0.75,
            prosody_score=prosody_score,
            energy_score=energy_score,
            speech_rate_score=speech_rate_score,
            indicators=indicators,
            recommendations=recommendations,
            change_from_baseline=change_from_baseline,
            created_at=datetime.now(timezone.utc)
        )

    async def _quick_assess(self, features: AudioFeatures) -> float:
        """Quick assessment for comparison."""
        score = 0
        if features.pitch_std < 20:
            score += 0.25
        if features.speech_rate < 3.5:
            score += 0.2
        if features.energy_mean < 0.05:
            score += 0.2
        return score

    def _generate_recommendations(
        self,
        severity: AssessmentSeverity,
        indicators: List[str]
    ) -> List[str]:
        """Generate recommendations based on assessment."""
        recommendations = []

        if severity == AssessmentSeverity.SEVERE:
            recommendations.extend([
                "Urgent mental health evaluation recommended",
                "Consider immediate psychiatric consultation",
                "Assess for suicidal ideation"
            ])
        elif severity == AssessmentSeverity.MODERATE:
            recommendations.extend([
                "Schedule mental health screening appointment",
                "Consider PHQ-9 questionnaire",
                "Discuss with primary care provider"
            ])
        elif severity == AssessmentSeverity.MILD:
            recommendations.extend([
                "Continue monitoring",
                "Consider wellness check-in",
                "Track mood changes"
            ])
        else:
            recommendations.append("No immediate concerns; continue routine monitoring")

        return recommendations


class CognitiveAssessor:
    """Assess cognitive function from voice."""

    async def assess(
        self,
        features: AudioFeatures,
        transcript: Optional[str] = None
    ) -> CognitiveAssessment:
        """Assess cognitive indicators from voice features."""

        # Fluency assessment
        fluency_score = self._calculate_fluency_score(features)

        # Word finding assessment
        word_finding_score = self._calculate_word_finding_score(features)

        # Coherence (would use transcript in production)
        coherence_score = 0.8  # Simulated

        # Memory indicators
        memory_indicators = self._assess_memory_indicators(features)

        # Calculate overall cognitive score
        cognitive_score = (
            fluency_score * 0.3 +
            word_finding_score * 0.3 +
            coherence_score * 0.2 +
            memory_indicators * 0.2
        ) * 100

        # Risk scores
        mci_risk = self._calculate_mci_risk(
            fluency_score, word_finding_score, memory_indicators
        )
        dementia_risk = mci_risk * 0.5  # Simplified

        # Determine severity
        if cognitive_score < 50:
            severity = AssessmentSeverity.SEVERE
        elif cognitive_score < 65:
            severity = AssessmentSeverity.MODERATE
        elif cognitive_score < 80:
            severity = AssessmentSeverity.MILD
        else:
            severity = AssessmentSeverity.NORMAL

        # Generate findings and recommendations
        findings = self._generate_findings(
            fluency_score, word_finding_score, memory_indicators
        )
        recommendations = self._generate_recommendations(severity, mci_risk)

        return CognitiveAssessment(
            assessment_id=uuid4(),
            cognitive_score=cognitive_score,
            severity=severity,
            confidence=0.70,
            fluency_score=fluency_score,
            word_finding_score=word_finding_score,
            coherence_score=coherence_score,
            memory_indicators=memory_indicators,
            mci_risk_score=mci_risk,
            dementia_risk_score=dementia_risk,
            findings=findings,
            recommendations=recommendations,
            created_at=datetime.now(timezone.utc)
        )

    def _calculate_fluency_score(self, features: AudioFeatures) -> float:
        """Calculate verbal fluency score."""
        # Higher speech rate and articulation = better fluency
        rate_score = min(features.speech_rate / 5.0, 1.0)
        articulation_score = min(features.articulation_rate / 5.5, 1.0)

        # Fewer pauses = better fluency
        pause_penalty = min(features.pause_frequency * 0.5, 0.3)

        return (rate_score + articulation_score) / 2 - pause_penalty

    def _calculate_word_finding_score(self, features: AudioFeatures) -> float:
        """Calculate word finding ability score."""
        # Fewer filled pauses and word-finding pauses = better
        filled_pause_penalty = min(features.filled_pause_count * 0.1, 0.4)
        wf_pause_penalty = features.word_finding_pauses * 0.2

        base_score = 1.0
        return max(0, base_score - filled_pause_penalty - wf_pause_penalty)

    def _assess_memory_indicators(self, features: AudioFeatures) -> float:
        """Assess memory-related speech indicators."""
        # Repetitions might indicate memory issues
        repetition_penalty = features.repetitions * 0.15

        # Longer pauses might indicate retrieval difficulty
        pause_penalty = max(0, (features.pause_duration_mean - 0.5) * 0.3)

        return max(0, 1.0 - repetition_penalty - pause_penalty)

    def _calculate_mci_risk(
        self,
        fluency: float,
        word_finding: float,
        memory: float
    ) -> float:
        """Calculate MCI risk score."""
        # Average of deficits
        avg_score = (fluency + word_finding + memory) / 3
        return max(0, min(1, 1 - avg_score))

    def _generate_findings(
        self,
        fluency: float,
        word_finding: float,
        memory: float
    ) -> List[str]:
        """Generate cognitive findings."""
        findings = []

        if fluency < 0.6:
            findings.append("Reduced verbal fluency detected")
        if word_finding < 0.6:
            findings.append("Word-finding difficulties observed")
        if memory < 0.6:
            findings.append("Possible memory retrieval issues")

        if not findings:
            findings.append("No significant cognitive concerns detected")

        return findings

    def _generate_recommendations(
        self,
        severity: AssessmentSeverity,
        mci_risk: float
    ) -> List[str]:
        """Generate cognitive recommendations."""
        recommendations = []

        if severity in [AssessmentSeverity.SEVERE, AssessmentSeverity.MODERATE]:
            recommendations.extend([
                "Comprehensive neuropsychological evaluation recommended",
                "Consider referral to neurology",
                "MoCA or MMSE screening advised"
            ])
        elif mci_risk > 0.3:
            recommendations.extend([
                "Continue monitoring cognitive function",
                "Consider periodic cognitive screening",
                "Encourage cognitive engagement activities"
            ])
        else:
            recommendations.append("Continue routine health maintenance")

        return recommendations


class RespiratoryAnalyzer:
    """Analyze respiratory health from voice."""

    async def assess(
        self,
        features: AudioFeatures,
        cough_audio: Optional[bytes] = None
    ) -> RespiratoryAssessment:
        """Assess respiratory health from voice characteristics."""

        # Breath support assessment
        breath_support = self._assess_breath_support(features)

        # Detect abnormal sounds (would use audio classification in production)
        cough_detected = False
        wheeze_detected = False
        stridor_detected = False

        # Calculate overall score
        respiratory_score = breath_support * 100

        # Determine breathing pattern
        breathing_pattern = self._determine_breathing_pattern(features)

        # Determine severity
        if respiratory_score < 50:
            severity = AssessmentSeverity.SEVERE
        elif respiratory_score < 70:
            severity = AssessmentSeverity.MODERATE
        elif respiratory_score < 85:
            severity = AssessmentSeverity.MILD
        else:
            severity = AssessmentSeverity.NORMAL

        # Generate findings and recommendations
        findings = self._generate_findings(
            breath_support, breathing_pattern, wheeze_detected
        )
        recommendations = self._generate_recommendations(severity, findings)

        return RespiratoryAssessment(
            assessment_id=uuid4(),
            respiratory_health_score=respiratory_score,
            severity=severity,
            confidence=0.72,
            breath_support_score=breath_support,
            cough_detected=cough_detected,
            wheeze_detected=wheeze_detected,
            stridor_detected=stridor_detected,
            breathing_pattern=breathing_pattern,
            findings=findings,
            recommendations=recommendations,
            created_at=datetime.now(timezone.utc)
        )

    def _assess_breath_support(self, features: AudioFeatures) -> float:
        """Assess breath support from voice features."""
        # Good breath support = stable energy, good HNR, normal speech rate
        energy_stability = 1 - min(features.energy_std / 0.1, 1.0)
        voice_quality = min(features.hnr / 25.0, 1.0)
        rate_score = min(features.speech_rate / 5.0, 1.0)

        return (energy_stability + voice_quality + rate_score) / 3

    def _determine_breathing_pattern(self, features: AudioFeatures) -> str:
        """Determine breathing pattern from features."""
        if features.pause_frequency > 0.5:
            return "Frequent breath pauses - may indicate respiratory effort"
        elif features.pause_duration_mean > 0.8:
            return "Prolonged breath pauses"
        else:
            return "Normal breathing pattern"

    def _generate_findings(
        self,
        breath_support: float,
        breathing_pattern: str,
        wheeze: bool
    ) -> List[str]:
        """Generate respiratory findings."""
        findings = []

        if breath_support < 0.6:
            findings.append("Reduced breath support detected")

        if "effort" in breathing_pattern.lower():
            findings.append("Increased respiratory effort noted")

        if wheeze:
            findings.append("Possible wheezing detected")

        if not findings:
            findings.append("No significant respiratory concerns detected")

        return findings

    def _generate_recommendations(
        self,
        severity: AssessmentSeverity,
        findings: List[str]
    ) -> List[str]:
        """Generate respiratory recommendations."""
        recommendations = []

        if severity == AssessmentSeverity.SEVERE:
            recommendations.extend([
                "Urgent pulmonary evaluation recommended",
                "Consider spirometry testing",
                "Check oxygen saturation"
            ])
        elif severity == AssessmentSeverity.MODERATE:
            recommendations.extend([
                "Schedule pulmonary function testing",
                "Review current respiratory medications",
                "Consider chest imaging if indicated"
            ])
        else:
            recommendations.append("Continue routine monitoring")

        return recommendations


class VoiceBiomarkerService:
    """Main voice biomarker analysis service."""

    def __init__(self):
        self.feature_extractor = AudioFeatureExtractor()
        self.depression_detector = DepressionDetector()
        self.cognitive_assessor = CognitiveAssessor()
        self.respiratory_analyzer = RespiratoryAnalyzer()

    async def analyze(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        assessments: Optional[List[VoiceBiomarkerType]] = None,
        baseline_features: Optional[AudioFeatures] = None
    ) -> VoiceBiomarkerResult:
        """Perform comprehensive voice biomarker analysis."""
        import time
        start_time = time.time()

        # Default to all assessments
        if assessments is None:
            assessments = [
                VoiceBiomarkerType.DEPRESSION,
                VoiceBiomarkerType.COGNITIVE_DECLINE,
                VoiceBiomarkerType.RESPIRATORY
            ]

        # Extract features
        features = await self.feature_extractor.extract_features(
            audio_data, sample_rate
        )

        # Perform assessments
        biomarker_scores = []
        depression_assessment = None
        cognitive_assessment = None
        respiratory_assessment = None

        if VoiceBiomarkerType.DEPRESSION in assessments:
            depression_assessment = await self.depression_detector.assess(
                features, baseline_features
            )
            biomarker_scores.append(BiomarkerScore(
                biomarker_type=VoiceBiomarkerType.DEPRESSION,
                score=depression_assessment.phq9_equivalent_score / 27 * 100,
                severity=depression_assessment.severity,
                confidence=depression_assessment.confidence,
                contributing_features=depression_assessment.indicators[:3],
                interpretation=f"PHQ-9 equivalent: {depression_assessment.phq9_equivalent_score}"
            ))

        if VoiceBiomarkerType.COGNITIVE_DECLINE in assessments:
            cognitive_assessment = await self.cognitive_assessor.assess(features)
            biomarker_scores.append(BiomarkerScore(
                biomarker_type=VoiceBiomarkerType.COGNITIVE_DECLINE,
                score=100 - cognitive_assessment.cognitive_score,  # Higher = more concern
                severity=cognitive_assessment.severity,
                confidence=cognitive_assessment.confidence,
                contributing_features=cognitive_assessment.findings[:3],
                interpretation=f"Cognitive score: {cognitive_assessment.cognitive_score:.0f}/100"
            ))

        if VoiceBiomarkerType.RESPIRATORY in assessments:
            respiratory_assessment = await self.respiratory_analyzer.assess(features)
            biomarker_scores.append(BiomarkerScore(
                biomarker_type=VoiceBiomarkerType.RESPIRATORY,
                score=100 - respiratory_assessment.respiratory_health_score,
                severity=respiratory_assessment.severity,
                confidence=respiratory_assessment.confidence,
                contributing_features=respiratory_assessment.findings[:3],
                interpretation=f"Respiratory score: {respiratory_assessment.respiratory_health_score:.0f}/100"
            ))

        # Calculate overall health indicator
        if biomarker_scores:
            overall_health = 100 - sum(s.score for s in biomarker_scores) / len(biomarker_scores)
        else:
            overall_health = 100

        # Identify priority concerns
        priority_concerns = [
            s.biomarker_type.value for s in biomarker_scores
            if s.severity in [AssessmentSeverity.MODERATE, AssessmentSeverity.SEVERE]
        ]

        # Compile recommendations
        recommendations = []
        if depression_assessment:
            recommendations.extend(depression_assessment.recommendations[:2])
        if cognitive_assessment:
            recommendations.extend(cognitive_assessment.recommendations[:2])
        if respiratory_assessment:
            recommendations.extend(respiratory_assessment.recommendations[:2])

        # Baseline comparison
        baseline_comparison = None
        trend_direction = None
        if baseline_features:
            baseline_comparison = {
                'pitch_change': features.pitch_mean - baseline_features.pitch_mean,
                'energy_change': features.energy_mean - baseline_features.energy_mean,
                'speech_rate_change': features.speech_rate - baseline_features.speech_rate
            }

        # Quality assessment (simulated)
        audio_quality_score = 0.85
        is_valid = audio_quality_score > 0.5

        processing_time = (time.time() - start_time) * 1000

        return VoiceBiomarkerResult(
            result_id=uuid4(),
            recording_id=str(uuid4()),
            recording_duration_seconds=30.0,  # Would be calculated
            audio_features=features,
            biomarker_scores=biomarker_scores,
            depression_assessment=depression_assessment,
            cognitive_assessment=cognitive_assessment,
            respiratory_assessment=respiratory_assessment,
            overall_health_indicator=overall_health,
            priority_concerns=priority_concerns,
            recommendations=recommendations[:5],
            baseline_comparison=baseline_comparison,
            trend_direction=trend_direction,
            audio_quality_score=audio_quality_score,
            is_valid_sample=is_valid,
            model_version="1.0.0",
            processing_time_ms=processing_time,
            created_at=datetime.now(timezone.utc)
        )


# Global instance
voice_biomarker_service = VoiceBiomarkerService()
