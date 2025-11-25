"""
Predictive Health Analytics Service

EPIC-010: Medical AI Capabilities
US-010.5: Predictive Health Analytics

Risk prediction models:
- Readmission risk prediction
- Deterioration early warning
- No-show prediction
- Disease progression modeling
- Length of stay prediction
- Risk factor identification
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4, UUID
import math


class RiskLevel(str, Enum):
    """Risk level categories."""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"


class PredictionType(str, Enum):
    """Types of predictions."""
    READMISSION_30DAY = "readmission_30day"
    READMISSION_90DAY = "readmission_90day"
    DETERIORATION = "deterioration"
    MORTALITY = "mortality"
    NO_SHOW = "no_show"
    LENGTH_OF_STAY = "length_of_stay"
    DISEASE_PROGRESSION = "disease_progression"
    FALL_RISK = "fall_risk"
    SEPSIS_RISK = "sepsis_risk"
    DECOMPENSATION = "decompensation"


class DeteriorationIndicator(str, Enum):
    """Indicators of clinical deterioration."""
    VITAL_SIGN_ABNORMALITY = "vital_sign_abnormality"
    LAB_TREND_CONCERNING = "lab_trend_concerning"
    MENTAL_STATUS_CHANGE = "mental_status_change"
    RESPIRATORY_DECLINE = "respiratory_decline"
    HEMODYNAMIC_INSTABILITY = "hemodynamic_instability"
    INCREASING_OXYGEN_REQUIREMENT = "increasing_oxygen_requirement"
    ACUTE_KIDNEY_INJURY = "acute_kidney_injury"


@dataclass
class RiskFactor:
    """Individual risk factor contribution."""
    factor_name: str
    factor_value: Any
    contribution: float  # Contribution to risk score (0-1)
    direction: str  # "increases" or "decreases"
    is_modifiable: bool
    recommendation: Optional[str] = None


@dataclass
class PredictionResult:
    """Risk prediction result."""
    prediction_id: UUID
    prediction_type: PredictionType
    risk_score: float  # 0.0 to 1.0
    risk_level: RiskLevel
    confidence: float

    # Risk factors
    top_risk_factors: List[RiskFactor]
    protective_factors: List[RiskFactor]

    # Predictions
    predicted_outcome: str
    probability: float
    confidence_interval: Tuple[float, float]

    # Recommendations
    recommended_interventions: List[str]
    monitoring_recommendations: List[str]

    # Time context
    prediction_window: str  # "30 days", "90 days", etc.
    valid_until: datetime

    # Model info
    model_version: str
    features_used: int
    created_at: datetime


@dataclass
class DeteriorationAlert:
    """Early warning alert for patient deterioration."""
    alert_id: UUID
    patient_id: UUID
    severity: str  # "critical", "warning", "watch"
    score: float  # Early warning score
    indicators: List[DeteriorationIndicator]
    trigger_values: Dict[str, Any]
    recommended_actions: List[str]
    time_to_event_hours: Optional[float]
    created_at: datetime


@dataclass
class DiseaseProgressionPrediction:
    """Disease progression prediction."""
    prediction_id: UUID
    condition: str
    current_stage: str
    predicted_stage: str
    time_to_progression_months: float
    confidence: float
    risk_factors: List[RiskFactor]
    recommendations: List[str]


class ReadmissionRiskModel:
    """30-day hospital readmission risk prediction model."""

    def __init__(self):
        # LACE+ score components (validated readmission model)
        self.lace_weights = {
            'length_of_stay': {
                1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 4, 7: 5, '7+': 5
            },
            'acuity': {  # Admission type
                'emergency': 3, 'urgent': 2, 'elective': 0
            },
            'comorbidity': {  # Charlson comorbidity index
                0: 0, 1: 1, 2: 2, 3: 3, '4+': 5
            },
            'ed_visits_6mo': {  # ED visits in past 6 months
                0: 0, 1: 1, 2: 2, 3: 3, '4+': 4
            }
        }

        # Additional risk factors
        self.additional_factors = {
            'age_over_65': 0.15,
            'lives_alone': 0.12,
            'heart_failure': 0.18,
            'copd': 0.15,
            'diabetes': 0.10,
            'chronic_kidney_disease': 0.14,
            'polypharmacy_10plus': 0.12,
            'prior_admission_30d': 0.25,
            'substance_use': 0.08,
            'depression': 0.10,
            'low_health_literacy': 0.08,
            'no_pcp': 0.10,
            'transportation_barrier': 0.06
        }

    async def predict_readmission_risk(
        self,
        patient_data: Dict[str, Any]
    ) -> PredictionResult:
        """Predict 30-day readmission risk."""

        # Calculate LACE score
        lace_score = self._calculate_lace_score(patient_data)

        # Calculate additional risk factors
        additional_risk = self._calculate_additional_risk(patient_data)

        # Combine scores (LACE contributes ~60%, additional factors ~40%)
        base_risk = (lace_score / 19) * 0.6  # Max LACE is ~19
        total_risk = min(0.95, base_risk + additional_risk * 0.4)

        # Identify top risk factors
        risk_factors = self._identify_risk_factors(patient_data, additional_risk)

        # Determine risk level
        risk_level = self._categorize_risk(total_risk)

        # Generate interventions
        interventions = self._generate_interventions(risk_factors, risk_level)

        # Calculate confidence interval
        ci_low = max(0, total_risk - 0.1)
        ci_high = min(1, total_risk + 0.1)

        return PredictionResult(
            prediction_id=uuid4(),
            prediction_type=PredictionType.READMISSION_30DAY,
            risk_score=total_risk,
            risk_level=risk_level,
            confidence=0.82,
            top_risk_factors=risk_factors[:5],
            protective_factors=self._identify_protective_factors(patient_data),
            predicted_outcome="Hospital readmission within 30 days",
            probability=total_risk,
            confidence_interval=(ci_low, ci_high),
            recommended_interventions=interventions,
            monitoring_recommendations=self._monitoring_recommendations(risk_level),
            prediction_window="30 days",
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            model_version="1.0.0",
            features_used=len(patient_data),
            created_at=datetime.now(timezone.utc)
        )

    def _calculate_lace_score(self, data: Dict) -> int:
        """Calculate LACE score component."""
        score = 0

        # Length of stay
        los = data.get('length_of_stay', 1)
        if los >= 7:
            score += 5
        elif los >= 4:
            score += los

        # Acuity (admission type)
        admission_type = data.get('admission_type', 'elective')
        score += self.lace_weights['acuity'].get(admission_type, 0)

        # Comorbidity (Charlson index)
        charlson = data.get('charlson_index', 0)
        if charlson >= 4:
            score += 5
        else:
            score += charlson

        # ED visits
        ed_visits = data.get('ed_visits_6_months', 0)
        if ed_visits >= 4:
            score += 4
        else:
            score += ed_visits

        return score

    def _calculate_additional_risk(self, data: Dict) -> float:
        """Calculate additional risk factors."""
        risk = 0.0

        conditions = data.get('conditions', [])
        conditions_lower = [c.lower() for c in conditions]

        # Age
        age = data.get('age', 0)
        if age > 65:
            risk += self.additional_factors['age_over_65']

        # Social factors
        if data.get('lives_alone', False):
            risk += self.additional_factors['lives_alone']

        # Conditions
        if any('heart failure' in c or 'chf' in c for c in conditions_lower):
            risk += self.additional_factors['heart_failure']
        if any('copd' in c for c in conditions_lower):
            risk += self.additional_factors['copd']
        if any('diabetes' in c for c in conditions_lower):
            risk += self.additional_factors['diabetes']
        if any('kidney' in c or 'ckd' in c for c in conditions_lower):
            risk += self.additional_factors['chronic_kidney_disease']

        # Polypharmacy
        med_count = data.get('medication_count', 0)
        if med_count >= 10:
            risk += self.additional_factors['polypharmacy_10plus']

        # Prior admission
        if data.get('prior_admission_30_days', False):
            risk += self.additional_factors['prior_admission_30d']

        # Mental health
        if any('depression' in c for c in conditions_lower):
            risk += self.additional_factors['depression']

        # Care access
        if not data.get('has_pcp', True):
            risk += self.additional_factors['no_pcp']

        return risk

    def _identify_risk_factors(
        self, data: Dict, risk_score: float
    ) -> List[RiskFactor]:
        """Identify individual risk factor contributions."""
        factors = []

        # Age
        age = data.get('age', 0)
        if age > 65:
            factors.append(RiskFactor(
                factor_name="Age over 65",
                factor_value=age,
                contribution=0.15,
                direction="increases",
                is_modifiable=False
            ))

        # Length of stay
        los = data.get('length_of_stay', 1)
        if los >= 4:
            factors.append(RiskFactor(
                factor_name="Extended length of stay",
                factor_value=f"{los} days",
                contribution=min(los * 0.03, 0.15),
                direction="increases",
                is_modifiable=False
            ))

        # Conditions
        conditions = data.get('conditions', [])
        for condition in conditions:
            if 'heart failure' in condition.lower():
                factors.append(RiskFactor(
                    factor_name="Heart failure",
                    factor_value=condition,
                    contribution=0.18,
                    direction="increases",
                    is_modifiable=False,
                    recommendation="Ensure cardiology follow-up within 7 days"
                ))
            elif 'copd' in condition.lower():
                factors.append(RiskFactor(
                    factor_name="COPD",
                    factor_value=condition,
                    contribution=0.15,
                    direction="increases",
                    is_modifiable=False,
                    recommendation="Schedule pulmonology follow-up"
                ))

        # Social factors
        if data.get('lives_alone', False):
            factors.append(RiskFactor(
                factor_name="Lives alone",
                factor_value=True,
                contribution=0.12,
                direction="increases",
                is_modifiable=True,
                recommendation="Consider home health services"
            ))

        # Medication burden
        med_count = data.get('medication_count', 0)
        if med_count >= 10:
            factors.append(RiskFactor(
                factor_name="Polypharmacy",
                factor_value=f"{med_count} medications",
                contribution=0.12,
                direction="increases",
                is_modifiable=True,
                recommendation="Medication reconciliation and deprescribing review"
            ))

        # Sort by contribution
        factors.sort(key=lambda x: x.contribution, reverse=True)
        return factors

    def _identify_protective_factors(self, data: Dict) -> List[RiskFactor]:
        """Identify protective factors."""
        factors = []

        if data.get('has_pcp', False):
            factors.append(RiskFactor(
                factor_name="Has primary care provider",
                factor_value=True,
                contribution=0.10,
                direction="decreases",
                is_modifiable=False
            ))

        if data.get('has_caregiver', False):
            factors.append(RiskFactor(
                factor_name="Has caregiver support",
                factor_value=True,
                contribution=0.08,
                direction="decreases",
                is_modifiable=False
            ))

        if data.get('follow_up_scheduled', False):
            factors.append(RiskFactor(
                factor_name="Follow-up appointment scheduled",
                factor_value=True,
                contribution=0.12,
                direction="decreases",
                is_modifiable=True
            ))

        return factors

    def _categorize_risk(self, risk_score: float) -> RiskLevel:
        """Categorize risk score into levels."""
        if risk_score >= 0.7:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MODERATE
        elif risk_score >= 0.15:
            return RiskLevel.LOW
        return RiskLevel.MINIMAL

    def _generate_interventions(
        self, factors: List[RiskFactor], risk_level: RiskLevel
    ) -> List[str]:
        """Generate recommended interventions."""
        interventions = []

        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            interventions.append("Enroll in transitional care management program")
            interventions.append("Schedule follow-up within 7 days of discharge")
            interventions.append("Medication reconciliation before discharge")
            interventions.append("Teach-back for discharge instructions")

        if risk_level == RiskLevel.CRITICAL:
            interventions.append("Consider home health services")
            interventions.append("Care manager assignment")

        # Factor-specific interventions
        for factor in factors:
            if factor.recommendation:
                interventions.append(factor.recommendation)

        return interventions[:8]

    def _monitoring_recommendations(self, risk_level: RiskLevel) -> List[str]:
        """Generate monitoring recommendations."""
        recommendations = ["Monitor for signs of clinical deterioration"]

        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            recommendations.extend([
                "Daily weight monitoring",
                "Track symptoms with patient diary",
                "Phone follow-up within 48-72 hours",
                "Ensure medication adherence"
            ])

        return recommendations


class DeteriorationDetector:
    """Early warning system for clinical deterioration."""

    def __init__(self):
        # Modified Early Warning Score (MEWS) thresholds
        self.mews_components = {
            'systolic_bp': {
                'ranges': [(0, 70, 3), (71, 80, 2), (81, 100, 1), (101, 199, 0), (200, 999, 2)],
            },
            'heart_rate': {
                'ranges': [(0, 40, 2), (41, 50, 1), (51, 100, 0), (101, 110, 1), (111, 129, 2), (130, 999, 3)],
            },
            'respiratory_rate': {
                'ranges': [(0, 8, 2), (9, 14, 0), (15, 20, 1), (21, 29, 2), (30, 999, 3)],
            },
            'temperature': {
                'ranges': [(0, 35, 2), (35.1, 38.4, 0), (38.5, 38.9, 1), (39, 999, 2)],
            },
            'consciousness': {
                'scores': {'alert': 0, 'voice': 1, 'pain': 2, 'unresponsive': 3}
            }
        }

    async def detect_deterioration(
        self,
        patient_id: UUID,
        current_vitals: Dict[str, Any],
        vital_trends: Optional[List[Dict]] = None,
        lab_trends: Optional[List[Dict]] = None
    ) -> DeteriorationAlert:
        """Detect early signs of clinical deterioration."""

        # Calculate MEWS
        mews_score = self._calculate_mews(current_vitals)

        # Analyze vital sign trends
        trend_indicators = self._analyze_vital_trends(vital_trends) if vital_trends else []

        # Analyze lab trends
        lab_indicators = self._analyze_lab_trends(lab_trends) if lab_trends else []

        # Combine indicators
        all_indicators = trend_indicators + lab_indicators

        # Determine severity
        severity = self._determine_severity(mews_score, all_indicators)

        # Estimate time to event
        time_to_event = self._estimate_time_to_event(mews_score, all_indicators)

        # Generate recommendations
        recommendations = self._generate_recommendations(severity, all_indicators)

        return DeteriorationAlert(
            alert_id=uuid4(),
            patient_id=patient_id,
            severity=severity,
            score=mews_score,
            indicators=all_indicators,
            trigger_values=current_vitals,
            recommended_actions=recommendations,
            time_to_event_hours=time_to_event,
            created_at=datetime.now(timezone.utc)
        )

    def _calculate_mews(self, vitals: Dict) -> float:
        """Calculate Modified Early Warning Score."""
        score = 0

        # Systolic BP
        sbp = vitals.get('systolic_bp') or vitals.get('systolic', 120)
        for low, high, points in self.mews_components['systolic_bp']['ranges']:
            if low <= sbp <= high:
                score += points
                break

        # Heart rate
        hr = vitals.get('heart_rate') or vitals.get('pulse', 80)
        for low, high, points in self.mews_components['heart_rate']['ranges']:
            if low <= hr <= high:
                score += points
                break

        # Respiratory rate
        rr = vitals.get('respiratory_rate', 16)
        for low, high, points in self.mews_components['respiratory_rate']['ranges']:
            if low <= rr <= high:
                score += points
                break

        # Temperature
        temp = vitals.get('temperature', 37)
        for low, high, points in self.mews_components['temperature']['ranges']:
            if low <= temp <= high:
                score += points
                break

        # Consciousness
        consciousness = vitals.get('consciousness', 'alert').lower()
        score += self.mews_components['consciousness']['scores'].get(consciousness, 0)

        return score

    def _analyze_vital_trends(
        self, trends: List[Dict]
    ) -> List[DeteriorationIndicator]:
        """Analyze vital sign trends for deterioration."""
        indicators = []

        if len(trends) < 2:
            return indicators

        # Check for declining trends
        recent = trends[-1]
        previous = trends[-2]

        # Check BP decline
        if recent.get('systolic_bp', 120) < previous.get('systolic_bp', 120) - 20:
            indicators.append(DeteriorationIndicator.HEMODYNAMIC_INSTABILITY)

        # Check HR increase
        if recent.get('heart_rate', 80) > previous.get('heart_rate', 80) + 20:
            indicators.append(DeteriorationIndicator.VITAL_SIGN_ABNORMALITY)

        # Check RR increase
        if recent.get('respiratory_rate', 16) > previous.get('respiratory_rate', 16) + 6:
            indicators.append(DeteriorationIndicator.RESPIRATORY_DECLINE)

        # Check O2 sat decline
        if recent.get('oxygen_saturation', 98) < previous.get('oxygen_saturation', 98) - 4:
            indicators.append(DeteriorationIndicator.INCREASING_OXYGEN_REQUIREMENT)

        return indicators

    def _analyze_lab_trends(
        self, trends: List[Dict]
    ) -> List[DeteriorationIndicator]:
        """Analyze lab trends for deterioration."""
        indicators = []

        if len(trends) < 2:
            return indicators

        recent = trends[-1]
        previous = trends[-2]

        # Check creatinine (AKI indicator)
        if recent.get('creatinine', 1.0) > previous.get('creatinine', 1.0) * 1.5:
            indicators.append(DeteriorationIndicator.ACUTE_KIDNEY_INJURY)

        # Check lactate
        if recent.get('lactate', 1.0) > 2.0:
            indicators.append(DeteriorationIndicator.LAB_TREND_CONCERNING)

        # Check WBC
        if recent.get('wbc', 8) > 15 or recent.get('wbc', 8) < 4:
            indicators.append(DeteriorationIndicator.LAB_TREND_CONCERNING)

        return indicators

    def _determine_severity(
        self, mews_score: float, indicators: List[DeteriorationIndicator]
    ) -> str:
        """Determine alert severity."""
        if mews_score >= 5 or len(indicators) >= 3:
            return "critical"
        elif mews_score >= 3 or len(indicators) >= 2:
            return "warning"
        elif mews_score >= 2 or len(indicators) >= 1:
            return "watch"
        return "normal"

    def _estimate_time_to_event(
        self, mews_score: float, indicators: List
    ) -> Optional[float]:
        """Estimate time to critical event in hours."""
        if mews_score >= 5:
            return 4.0  # 4 hours
        elif mews_score >= 3:
            return 12.0  # 12 hours
        elif mews_score >= 2:
            return 24.0  # 24 hours
        return None

    def _generate_recommendations(
        self, severity: str, indicators: List
    ) -> List[str]:
        """Generate action recommendations."""
        recommendations = []

        if severity == "critical":
            recommendations.extend([
                "Immediate physician notification required",
                "Prepare for potential rapid response",
                "Increase monitoring frequency to q15 minutes",
                "Verify IV access and prepare for intervention"
            ])
        elif severity == "warning":
            recommendations.extend([
                "Notify covering physician",
                "Increase monitoring frequency to q1 hour",
                "Review current orders and medications"
            ])
        else:
            recommendations.extend([
                "Continue routine monitoring",
                "Document and reassess in 4 hours"
            ])

        # Indicator-specific recommendations
        if DeteriorationIndicator.RESPIRATORY_DECLINE in indicators:
            recommendations.append("Assess respiratory status, consider respiratory therapy")
        if DeteriorationIndicator.ACUTE_KIDNEY_INJURY in indicators:
            recommendations.append("Review nephrotoxic medications, check fluid status")

        return recommendations


class NoShowPredictor:
    """Predict appointment no-show probability."""

    def __init__(self):
        self.risk_factors = {
            'prior_no_shows': 0.25,  # Strong predictor
            'lead_time_days': 0.02,  # Per day
            'new_patient': 0.08,
            'monday_appointment': 0.05,
            'afternoon_appointment': 0.03,
            'transportation_barrier': 0.15,
            'mental_health_visit': 0.10,
            'no_reminder': 0.12,
            'long_wait_time_prev': 0.08
        }

    async def predict_no_show(
        self,
        appointment_data: Dict[str, Any]
    ) -> PredictionResult:
        """Predict probability of no-show."""
        base_rate = 0.15  # Base no-show rate ~15%

        # Calculate risk
        risk = base_rate

        # Prior no-shows (strongest predictor)
        prior_no_shows = appointment_data.get('prior_no_shows', 0)
        risk += min(prior_no_shows * self.risk_factors['prior_no_shows'], 0.5)

        # Lead time
        lead_time = appointment_data.get('lead_time_days', 7)
        risk += min(lead_time * self.risk_factors['lead_time_days'], 0.15)

        # Patient factors
        if appointment_data.get('is_new_patient', False):
            risk += self.risk_factors['new_patient']

        if appointment_data.get('transportation_barrier', False):
            risk += self.risk_factors['transportation_barrier']

        # Appointment factors
        appointment_day = appointment_data.get('day_of_week', '')
        if appointment_day.lower() == 'monday':
            risk += self.risk_factors['monday_appointment']

        appointment_time = appointment_data.get('time_slot', '')
        if 'afternoon' in appointment_time.lower():
            risk += self.risk_factors['afternoon_appointment']

        if not appointment_data.get('reminder_sent', True):
            risk += self.risk_factors['no_reminder']

        risk = min(0.95, risk)
        risk_level = self._categorize_risk(risk)

        # Generate interventions
        interventions = self._generate_interventions(
            appointment_data, risk_level
        )

        return PredictionResult(
            prediction_id=uuid4(),
            prediction_type=PredictionType.NO_SHOW,
            risk_score=risk,
            risk_level=risk_level,
            confidence=0.75,
            top_risk_factors=self._identify_factors(appointment_data),
            protective_factors=[],
            predicted_outcome="Appointment no-show",
            probability=risk,
            confidence_interval=(max(0, risk - 0.1), min(1, risk + 0.1)),
            recommended_interventions=interventions,
            monitoring_recommendations=["Track no-show patterns"],
            prediction_window="Until appointment",
            valid_until=appointment_data.get('appointment_datetime', datetime.now(timezone.utc)),
            model_version="1.0.0",
            features_used=len(appointment_data),
            created_at=datetime.now(timezone.utc)
        )

    def _categorize_risk(self, risk: float) -> RiskLevel:
        """Categorize no-show risk."""
        if risk >= 0.5:
            return RiskLevel.HIGH
        elif risk >= 0.3:
            return RiskLevel.MODERATE
        elif risk >= 0.2:
            return RiskLevel.LOW
        return RiskLevel.MINIMAL

    def _identify_factors(self, data: Dict) -> List[RiskFactor]:
        """Identify no-show risk factors."""
        factors = []

        if data.get('prior_no_shows', 0) > 0:
            factors.append(RiskFactor(
                factor_name="History of no-shows",
                factor_value=data['prior_no_shows'],
                contribution=0.25,
                direction="increases",
                is_modifiable=False,
                recommendation="Implement overbooking strategy"
            ))

        if data.get('lead_time_days', 0) > 14:
            factors.append(RiskFactor(
                factor_name="Long lead time",
                factor_value=f"{data['lead_time_days']} days",
                contribution=0.15,
                direction="increases",
                is_modifiable=True,
                recommendation="Send reminder closer to appointment"
            ))

        return factors

    def _generate_interventions(
        self, data: Dict, risk_level: RiskLevel
    ) -> List[str]:
        """Generate interventions to reduce no-show risk."""
        interventions = []

        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            interventions.extend([
                "Send multiple reminders (SMS + phone call)",
                "Confirm appointment 24-48 hours before",
                "Offer telehealth alternative",
                "Consider double-booking slot"
            ])

        if data.get('transportation_barrier', False):
            interventions.append("Offer transportation assistance")

        if risk_level == RiskLevel.MODERATE:
            interventions.extend([
                "Send automated reminder",
                "Offer easy rescheduling option"
            ])

        return interventions


class PredictiveAnalyticsService:
    """Main predictive analytics service."""

    def __init__(self):
        self.readmission_model = ReadmissionRiskModel()
        self.deterioration_detector = DeteriorationDetector()
        self.no_show_predictor = NoShowPredictor()

    async def predict_readmission_risk(
        self, patient_data: Dict[str, Any]
    ) -> PredictionResult:
        """Predict hospital readmission risk."""
        return await self.readmission_model.predict_readmission_risk(patient_data)

    async def detect_deterioration(
        self,
        patient_id: UUID,
        current_vitals: Dict[str, Any],
        vital_trends: Optional[List[Dict]] = None,
        lab_trends: Optional[List[Dict]] = None
    ) -> DeteriorationAlert:
        """Detect clinical deterioration."""
        return await self.deterioration_detector.detect_deterioration(
            patient_id, current_vitals, vital_trends, lab_trends
        )

    async def predict_no_show(
        self, appointment_data: Dict[str, Any]
    ) -> PredictionResult:
        """Predict appointment no-show probability."""
        return await self.no_show_predictor.predict_no_show(appointment_data)

    async def calculate_fall_risk(
        self, patient_data: Dict[str, Any]
    ) -> PredictionResult:
        """Calculate fall risk using Morse Fall Scale."""
        score = 0

        # History of falling
        if patient_data.get('history_of_falls', False):
            score += 25

        # Secondary diagnosis
        if patient_data.get('secondary_diagnosis', False):
            score += 15

        # Ambulatory aid
        aid_type = patient_data.get('ambulatory_aid', 'none')
        if aid_type == 'furniture':
            score += 30
        elif aid_type in ['crutches', 'cane', 'walker']:
            score += 15

        # IV/Heparin lock
        if patient_data.get('iv_therapy', False):
            score += 20

        # Gait
        gait = patient_data.get('gait', 'normal')
        if gait == 'impaired':
            score += 10
        elif gait == 'weak':
            score += 20

        # Mental status
        if patient_data.get('forgets_limitations', False):
            score += 15

        risk_score = score / 125  # Normalize to 0-1

        if risk_score >= 0.45:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.25:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW

        return PredictionResult(
            prediction_id=uuid4(),
            prediction_type=PredictionType.FALL_RISK,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=0.85,
            top_risk_factors=[],
            protective_factors=[],
            predicted_outcome="Fall event",
            probability=risk_score,
            confidence_interval=(max(0, risk_score - 0.1), min(1, risk_score + 0.1)),
            recommended_interventions=[
                "Implement fall precautions",
                "Ensure call light within reach",
                "Non-slip footwear",
                "Bed alarm if high risk"
            ] if risk_level == RiskLevel.HIGH else [],
            monitoring_recommendations=["Reassess fall risk daily"],
            prediction_window="During hospitalization",
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            model_version="Morse Fall Scale",
            features_used=6,
            created_at=datetime.now(timezone.utc)
        )


# Global instance
predictive_analytics_service = PredictiveAnalyticsService()
