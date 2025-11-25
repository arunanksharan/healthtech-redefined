"""
Predictive Analytics Engine - EPIC-011: US-011.6
Builds and deploys predictive models for healthcare analytics.

Features:
- Readmission risk prediction
- Length of stay forecasting
- No-show prediction
- Disease progression modeling
- Cost prediction algorithms
- Model versioning and governance
- A/B testing framework
- Model performance monitoring
- Automated retraining pipelines
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from uuid import UUID, uuid4
import random
import math


class ModelType(Enum):
    """Types of predictive models."""
    READMISSION = "readmission"
    LENGTH_OF_STAY = "length_of_stay"
    NO_SHOW = "no_show"
    DETERIORATION = "deterioration"
    COST = "cost"
    MORTALITY = "mortality"
    SEPSIS = "sepsis"
    FALL_RISK = "fall_risk"


class ModelStatus(Enum):
    """Model deployment status."""
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class PredictionConfidence(Enum):
    """Confidence levels for predictions."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass
class ModelMetadata:
    """Metadata for a predictive model."""
    model_id: str
    model_type: ModelType
    name: str
    version: str
    status: ModelStatus
    created_at: datetime
    updated_at: datetime
    created_by: str
    description: str
    algorithm: str
    feature_count: int
    training_samples: int
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class FeatureImportance:
    """Feature importance data."""
    feature_name: str
    importance_score: float
    direction: str  # positive, negative
    category: str
    description: str


@dataclass
class PredictionResult:
    """Result from a prediction."""
    prediction_id: str
    model_id: str
    model_version: str
    patient_id: str
    prediction_type: ModelType
    predicted_value: float
    confidence: PredictionConfidence
    confidence_score: float
    risk_level: str
    threshold_used: float
    feature_contributions: List[FeatureImportance]
    recommended_actions: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None


@dataclass
class BatchPredictionJob:
    """Batch prediction job tracking."""
    job_id: str
    model_id: str
    status: str  # queued, running, completed, failed
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    output_location: Optional[str]
    error_message: Optional[str] = None


@dataclass
class ModelPerformance:
    """Model performance metrics."""
    model_id: str
    model_version: str
    evaluation_date: date
    dataset_type: str  # training, validation, test, production
    sample_size: int
    auc_roc: float
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    calibration_error: float
    lift_at_10: float
    confusion_matrix: Dict[str, int] = field(default_factory=dict)


@dataclass
class DriftMetrics:
    """Model drift detection metrics."""
    model_id: str
    detection_date: datetime
    feature_drift: Dict[str, float]
    prediction_drift: float
    label_drift: Optional[float]
    is_drifting: bool
    drift_severity: str  # none, low, medium, high
    recommended_action: str


@dataclass
class ABTestResult:
    """A/B test results."""
    test_id: str
    test_name: str
    model_a_id: str
    model_b_id: str
    start_date: date
    end_date: Optional[date]
    status: str  # running, completed, stopped
    traffic_split: float  # Percentage to model B
    model_a_samples: int
    model_b_samples: int
    model_a_metrics: Dict[str, float]
    model_b_metrics: Dict[str, float]
    winner: Optional[str]
    statistical_significance: float
    recommendation: str


@dataclass
class RetrainingJob:
    """Model retraining job."""
    job_id: str
    model_id: str
    trigger: str  # scheduled, drift_detected, manual
    status: str
    training_samples: int
    validation_samples: int
    started_at: datetime
    completed_at: Optional[datetime]
    new_version: Optional[str]
    performance_comparison: Dict[str, Dict[str, float]] = field(default_factory=dict)
    approved_for_deployment: bool = False


class PredictiveAnalyticsEngine:
    """
    Engine for predictive analytics model management and execution.

    Provides model deployment, prediction serving, performance monitoring,
    drift detection, and automated retraining capabilities.
    """

    def __init__(self):
        self.models: Dict[str, ModelMetadata] = {}
        self._initialize_models()
        self._cache: Dict[str, Any] = {}

    def _initialize_models(self):
        """Initialize default models."""
        model_configs = [
            (ModelType.READMISSION, "30-Day Readmission Predictor", "XGBoost", 0.82),
            (ModelType.LENGTH_OF_STAY, "Length of Stay Predictor", "LightGBM", 0.78),
            (ModelType.NO_SHOW, "Appointment No-Show Predictor", "Random Forest", 0.85),
            (ModelType.DETERIORATION, "Clinical Deterioration Model", "Neural Network", 0.88),
            (ModelType.COST, "Cost Prediction Model", "Gradient Boosting", 0.75),
            (ModelType.MORTALITY, "In-Hospital Mortality Risk", "Ensemble", 0.90),
            (ModelType.SEPSIS, "Sepsis Early Warning", "LSTM", 0.86),
            (ModelType.FALL_RISK, "Patient Fall Risk", "Logistic Regression", 0.79),
        ]

        for model_type, name, algorithm, auc in model_configs:
            model_id = f"MDL-{model_type.value.upper()}-001"
            self.models[model_id] = ModelMetadata(
                model_id=model_id,
                model_type=model_type,
                name=name,
                version="1.0.0",
                status=ModelStatus.PRODUCTION,
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 6, 1),
                created_by="ML Team",
                description=f"Production {name}",
                algorithm=algorithm,
                feature_count=random.randint(25, 75),
                training_samples=random.randint(50000, 200000),
                performance_metrics={
                    "auc_roc": auc,
                    "precision": round(auc - random.uniform(0.05, 0.15), 3),
                    "recall": round(auc - random.uniform(0.03, 0.10), 3),
                    "f1_score": round(auc - random.uniform(0.05, 0.12), 3)
                },
                tags=["healthcare", model_type.value, "production"]
            )

    async def get_models(
        self,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
        tenant_id: Optional[str] = None
    ) -> List[ModelMetadata]:
        """
        Get available prediction models.

        Args:
            model_type: Filter by model type
            status: Filter by status
            tenant_id: Tenant ID

        Returns:
            List of model metadata
        """
        models = list(self.models.values())

        if model_type:
            models = [m for m in models if m.model_type == model_type]
        if status:
            models = [m for m in models if m.status == status]

        return models

    async def predict(
        self,
        model_type: ModelType,
        patient_id: str,
        features: Dict[str, Any],
        include_explanations: bool = True,
        tenant_id: Optional[str] = None
    ) -> PredictionResult:
        """
        Make a prediction for a patient.

        Args:
            model_type: Type of prediction
            patient_id: Patient identifier
            features: Input features for prediction
            include_explanations: Include feature explanations
            tenant_id: Tenant ID

        Returns:
            Prediction result with confidence and explanations
        """
        # Find the production model
        model = next(
            (m for m in self.models.values()
             if m.model_type == model_type and m.status == ModelStatus.PRODUCTION),
            None
        )

        if not model:
            raise ValueError(f"No production model found for {model_type.value}")

        # Simulate prediction
        random.seed(hash(patient_id + str(datetime.utcnow().date())))

        # Generate prediction based on features
        base_risk = self._calculate_base_risk(model_type, features)
        predicted_value = min(1.0, max(0.0, base_risk + random.uniform(-0.1, 0.1)))

        # Determine confidence
        if predicted_value > 0.8 or predicted_value < 0.2:
            confidence = PredictionConfidence.HIGH
            confidence_score = 0.85 + random.uniform(0, 0.10)
        elif predicted_value > 0.6 or predicted_value < 0.4:
            confidence = PredictionConfidence.MEDIUM
            confidence_score = 0.70 + random.uniform(0, 0.15)
        else:
            confidence = PredictionConfidence.LOW
            confidence_score = 0.55 + random.uniform(0, 0.15)

        # Risk level
        if predicted_value >= 0.7:
            risk_level = "high"
        elif predicted_value >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Feature contributions
        contributions = []
        if include_explanations:
            contributions = self._generate_feature_contributions(model_type, features, predicted_value)

        # Recommendations
        recommendations = self._generate_recommendations(model_type, risk_level, predicted_value)

        return PredictionResult(
            prediction_id=str(uuid4()),
            model_id=model.model_id,
            model_version=model.version,
            patient_id=patient_id,
            prediction_type=model_type,
            predicted_value=round(predicted_value, 4),
            confidence=confidence,
            confidence_score=round(confidence_score, 3),
            risk_level=risk_level,
            threshold_used=0.5,
            feature_contributions=contributions,
            recommended_actions=recommendations,
            valid_until=datetime.utcnow() + timedelta(hours=24)
        )

    def _calculate_base_risk(
        self,
        model_type: ModelType,
        features: Dict[str, Any]
    ) -> float:
        """Calculate base risk from features."""
        base = 0.3

        # Age factor
        age = features.get("age", 50)
        if age > 75:
            base += 0.2
        elif age > 65:
            base += 0.1

        # Comorbidity count
        comorbidities = features.get("comorbidity_count", 0)
        base += min(0.3, comorbidities * 0.05)

        # Recent utilization
        if features.get("ed_visits_past_year", 0) > 2:
            base += 0.1
        if features.get("admissions_past_year", 0) > 1:
            base += 0.15

        # Model-specific adjustments
        if model_type == ModelType.NO_SHOW:
            if features.get("prior_no_shows", 0) > 0:
                base += 0.2
            if features.get("appointment_lead_days", 7) > 14:
                base += 0.1

        elif model_type == ModelType.READMISSION:
            if features.get("length_of_stay", 3) > 7:
                base += 0.1
            if features.get("discharge_to_snf", False):
                base += 0.05

        return min(1.0, base)

    def _generate_feature_contributions(
        self,
        model_type: ModelType,
        features: Dict[str, Any],
        prediction: float
    ) -> List[FeatureImportance]:
        """Generate feature contribution explanations."""
        feature_definitions = {
            ModelType.READMISSION: [
                ("age", "Demographics", "Patient age in years"),
                ("length_of_stay", "Hospitalization", "Days in hospital"),
                ("comorbidity_count", "Clinical", "Number of chronic conditions"),
                ("ed_visits_past_year", "Utilization", "ED visits in past 12 months"),
                ("medication_count", "Medications", "Number of discharge medications"),
                ("discharge_disposition", "Discharge", "Discharge destination"),
            ],
            ModelType.NO_SHOW: [
                ("prior_no_shows", "History", "Previous no-show count"),
                ("appointment_lead_days", "Scheduling", "Days until appointment"),
                ("distance_to_clinic", "Access", "Distance to clinic in miles"),
                ("insurance_type", "Insurance", "Type of insurance coverage"),
                ("time_of_day", "Scheduling", "Appointment time slot"),
            ],
            ModelType.LENGTH_OF_STAY: [
                ("admission_type", "Admission", "Type of admission"),
                ("diagnosis_severity", "Clinical", "Severity of primary diagnosis"),
                ("age", "Demographics", "Patient age"),
                ("surgery_planned", "Procedures", "Planned surgical procedures"),
                ("comorbidity_score", "Clinical", "Elixhauser comorbidity score"),
            ]
        }

        definitions = feature_definitions.get(model_type, feature_definitions[ModelType.READMISSION])
        contributions = []

        for feat_name, category, description in definitions:
            importance = random.uniform(0.05, 0.25)
            direction = "positive" if random.random() > 0.5 else "negative"

            contributions.append(FeatureImportance(
                feature_name=feat_name,
                importance_score=round(importance, 3),
                direction=direction,
                category=category,
                description=description
            ))

        # Sort by importance
        contributions.sort(key=lambda x: x.importance_score, reverse=True)
        return contributions[:5]  # Top 5

    def _generate_recommendations(
        self,
        model_type: ModelType,
        risk_level: str,
        prediction: float
    ) -> List[str]:
        """Generate recommended actions based on prediction."""
        recommendations_map = {
            ModelType.READMISSION: {
                "high": [
                    "Schedule follow-up appointment within 48 hours",
                    "Initiate transitional care management",
                    "Conduct comprehensive medication reconciliation",
                    "Arrange home health services evaluation",
                    "Enroll in post-discharge care program"
                ],
                "medium": [
                    "Schedule follow-up within 7 days",
                    "Provide enhanced discharge education",
                    "Set up telehealth check-in at 72 hours",
                    "Review medication adherence plan"
                ],
                "low": [
                    "Standard follow-up care",
                    "Provide patient portal access",
                    "Schedule routine follow-up"
                ]
            },
            ModelType.NO_SHOW: {
                "high": [
                    "Send multiple appointment reminders",
                    "Offer transportation assistance",
                    "Consider telehealth alternative",
                    "Call patient day before appointment",
                    "Add to no-show prevention program"
                ],
                "medium": [
                    "Send text and email reminders",
                    "Confirm appointment 48 hours prior",
                    "Offer schedule change option"
                ],
                "low": [
                    "Standard reminder workflow"
                ]
            },
            ModelType.DETERIORATION: {
                "high": [
                    "Increase monitoring frequency",
                    "Alert rapid response team",
                    "Consider ICU transfer evaluation",
                    "Notify attending physician immediately"
                ],
                "medium": [
                    "Increase vital sign monitoring",
                    "Review current treatment plan",
                    "Consider specialty consultation"
                ],
                "low": [
                    "Continue standard monitoring"
                ]
            }
        }

        recs = recommendations_map.get(model_type, recommendations_map[ModelType.READMISSION])
        return recs.get(risk_level, recs["low"])

    async def batch_predict(
        self,
        model_type: ModelType,
        patient_ids: List[str],
        tenant_id: Optional[str] = None
    ) -> BatchPredictionJob:
        """
        Submit a batch prediction job.

        Args:
            model_type: Type of prediction
            patient_ids: List of patient IDs
            tenant_id: Tenant ID

        Returns:
            Batch job status
        """
        job_id = str(uuid4())[:8]

        return BatchPredictionJob(
            job_id=f"BATCH-{job_id}",
            model_id=f"MDL-{model_type.value.upper()}-001",
            status="completed",
            total_records=len(patient_ids),
            processed_records=len(patient_ids),
            successful_records=len(patient_ids) - random.randint(0, max(1, len(patient_ids) // 20)),
            failed_records=random.randint(0, max(1, len(patient_ids) // 20)),
            started_at=datetime.utcnow() - timedelta(minutes=5),
            completed_at=datetime.utcnow(),
            output_location=f"/predictions/batch/{job_id}/results.parquet"
        )

    async def get_model_performance(
        self,
        model_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get model performance metrics over time.

        Args:
            model_id: Model identifier
            start_date: Start date for metrics
            end_date: End date for metrics
            tenant_id: Tenant ID

        Returns:
            Performance metrics and trends
        """
        model = self.models.get(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")

        random.seed(hash(model_id))

        # Generate performance history
        days = 30
        history = []
        base_auc = model.performance_metrics.get("auc_roc", 0.80)

        for i in range(days):
            eval_date = date.today() - timedelta(days=days - i - 1)
            daily_auc = base_auc + random.uniform(-0.03, 0.03)

            history.append(ModelPerformance(
                model_id=model_id,
                model_version=model.version,
                evaluation_date=eval_date,
                dataset_type="production",
                sample_size=random.randint(500, 2000),
                auc_roc=round(daily_auc, 4),
                precision=round(daily_auc - random.uniform(0.05, 0.10), 4),
                recall=round(daily_auc - random.uniform(0.03, 0.08), 4),
                f1_score=round(daily_auc - random.uniform(0.04, 0.09), 4),
                accuracy=round(daily_auc - random.uniform(0.02, 0.07), 4),
                calibration_error=round(random.uniform(0.02, 0.08), 4),
                lift_at_10=round(random.uniform(2.5, 4.0), 2),
                confusion_matrix={
                    "true_positive": random.randint(300, 600),
                    "true_negative": random.randint(800, 1200),
                    "false_positive": random.randint(50, 150),
                    "false_negative": random.randint(50, 150)
                }
            ))

        return {
            "model": {
                "id": model.model_id,
                "name": model.name,
                "version": model.version,
                "status": model.status.value
            },
            "current_performance": {
                "auc_roc": history[-1].auc_roc,
                "precision": history[-1].precision,
                "recall": history[-1].recall,
                "f1_score": history[-1].f1_score,
                "accuracy": history[-1].accuracy,
                "sample_size": sum(h.sample_size for h in history)
            },
            "trends": {
                "auc_roc": [{"date": h.evaluation_date.isoformat(), "value": h.auc_roc} for h in history],
                "precision": [{"date": h.evaluation_date.isoformat(), "value": h.precision} for h in history],
                "recall": [{"date": h.evaluation_date.isoformat(), "value": h.recall} for h in history]
            },
            "alerts": [
                {"level": "info", "message": "Model performing within expected range"}
            ] if history[-1].auc_roc > base_auc - 0.05 else [
                {"level": "warning", "message": "Model performance degradation detected"}
            ]
        }

    async def detect_drift(
        self,
        model_id: str,
        tenant_id: Optional[str] = None
    ) -> DriftMetrics:
        """
        Detect model drift.

        Args:
            model_id: Model identifier
            tenant_id: Tenant ID

        Returns:
            Drift detection results
        """
        random.seed(hash(model_id + str(datetime.utcnow().date())))

        # Simulate drift detection
        feature_drift = {
            "age": round(random.uniform(0, 0.15), 3),
            "comorbidity_count": round(random.uniform(0, 0.20), 3),
            "length_of_stay": round(random.uniform(0, 0.12), 3),
            "ed_visits": round(random.uniform(0, 0.18), 3),
        }

        prediction_drift = round(random.uniform(0, 0.15), 3)
        max_drift = max(list(feature_drift.values()) + [prediction_drift])

        if max_drift > 0.15:
            severity = "high"
            is_drifting = True
            action = "Immediate model retraining recommended"
        elif max_drift > 0.10:
            severity = "medium"
            is_drifting = True
            action = "Schedule model retraining within 7 days"
        elif max_drift > 0.05:
            severity = "low"
            is_drifting = False
            action = "Continue monitoring, no action required"
        else:
            severity = "none"
            is_drifting = False
            action = "No drift detected"

        return DriftMetrics(
            model_id=model_id,
            detection_date=datetime.utcnow(),
            feature_drift=feature_drift,
            prediction_drift=prediction_drift,
            label_drift=round(random.uniform(0, 0.10), 3),
            is_drifting=is_drifting,
            drift_severity=severity,
            recommended_action=action
        )

    async def create_ab_test(
        self,
        test_name: str,
        model_a_id: str,
        model_b_id: str,
        traffic_split: float = 0.5,
        tenant_id: Optional[str] = None
    ) -> ABTestResult:
        """
        Create an A/B test between two models.

        Args:
            test_name: Name of the test
            model_a_id: Control model ID
            model_b_id: Challenger model ID
            traffic_split: Percentage of traffic to model B
            tenant_id: Tenant ID

        Returns:
            A/B test configuration
        """
        test_id = str(uuid4())[:8]

        return ABTestResult(
            test_id=f"AB-{test_id}",
            test_name=test_name,
            model_a_id=model_a_id,
            model_b_id=model_b_id,
            start_date=date.today(),
            end_date=None,
            status="running",
            traffic_split=traffic_split,
            model_a_samples=0,
            model_b_samples=0,
            model_a_metrics={},
            model_b_metrics={},
            winner=None,
            statistical_significance=0.0,
            recommendation="Test in progress, continue collecting data"
        )

    async def get_ab_test_results(
        self,
        test_id: str,
        tenant_id: Optional[str] = None
    ) -> ABTestResult:
        """Get A/B test results."""
        random.seed(hash(test_id))

        # Simulate test results
        a_samples = random.randint(5000, 10000)
        b_samples = int(a_samples * random.uniform(0.45, 0.55))

        a_auc = 0.82 + random.uniform(-0.02, 0.02)
        b_auc = a_auc + random.uniform(-0.03, 0.05)

        significance = random.uniform(0.85, 0.99) if abs(b_auc - a_auc) > 0.02 else random.uniform(0.50, 0.85)

        winner = None
        recommendation = "Continue testing, not yet statistically significant"

        if significance > 0.95:
            if b_auc > a_auc:
                winner = "model_b"
                recommendation = "Deploy Model B to production"
            else:
                winner = "model_a"
                recommendation = "Keep Model A in production"

        return ABTestResult(
            test_id=test_id,
            test_name=f"Test {test_id}",
            model_a_id="MDL-READMISSION-001",
            model_b_id="MDL-READMISSION-002",
            start_date=date.today() - timedelta(days=14),
            end_date=date.today() if winner else None,
            status="completed" if winner else "running",
            traffic_split=0.5,
            model_a_samples=a_samples,
            model_b_samples=b_samples,
            model_a_metrics={"auc_roc": round(a_auc, 4), "precision": round(a_auc - 0.05, 4)},
            model_b_metrics={"auc_roc": round(b_auc, 4), "precision": round(b_auc - 0.04, 4)},
            winner=winner,
            statistical_significance=round(significance, 3),
            recommendation=recommendation
        )

    async def trigger_retraining(
        self,
        model_id: str,
        trigger: str = "manual",
        tenant_id: Optional[str] = None
    ) -> RetrainingJob:
        """
        Trigger model retraining.

        Args:
            model_id: Model to retrain
            trigger: Trigger type (manual, scheduled, drift_detected)
            tenant_id: Tenant ID

        Returns:
            Retraining job status
        """
        job_id = str(uuid4())[:8]

        return RetrainingJob(
            job_id=f"RETRAIN-{job_id}",
            model_id=model_id,
            trigger=trigger,
            status="queued",
            training_samples=random.randint(80000, 150000),
            validation_samples=random.randint(15000, 30000),
            started_at=datetime.utcnow(),
            completed_at=None,
            new_version=None,
            performance_comparison={},
            approved_for_deployment=False
        )

    async def get_feature_store(
        self,
        model_type: ModelType,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get feature definitions for a model type."""
        feature_stores = {
            ModelType.READMISSION: {
                "feature_group": "readmission_features",
                "features": [
                    {"name": "age", "type": "numeric", "source": "patient_demographics"},
                    {"name": "gender", "type": "categorical", "source": "patient_demographics"},
                    {"name": "length_of_stay", "type": "numeric", "source": "encounter"},
                    {"name": "admission_type", "type": "categorical", "source": "encounter"},
                    {"name": "comorbidity_count", "type": "numeric", "source": "diagnoses"},
                    {"name": "medication_count", "type": "numeric", "source": "medications"},
                    {"name": "ed_visits_12m", "type": "numeric", "source": "utilization"},
                    {"name": "admissions_12m", "type": "numeric", "source": "utilization"},
                    {"name": "discharge_disposition", "type": "categorical", "source": "encounter"},
                    {"name": "primary_diagnosis_ccs", "type": "categorical", "source": "diagnoses"},
                ],
                "freshness": "daily",
                "last_updated": datetime.utcnow().isoformat()
            },
            ModelType.NO_SHOW: {
                "feature_group": "no_show_features",
                "features": [
                    {"name": "prior_no_shows", "type": "numeric", "source": "appointments"},
                    {"name": "lead_time_days", "type": "numeric", "source": "appointments"},
                    {"name": "appointment_hour", "type": "numeric", "source": "appointments"},
                    {"name": "provider_id", "type": "categorical", "source": "appointments"},
                    {"name": "visit_type", "type": "categorical", "source": "appointments"},
                    {"name": "distance_miles", "type": "numeric", "source": "patient_demographics"},
                    {"name": "insurance_type", "type": "categorical", "source": "patient_demographics"},
                ],
                "freshness": "real-time",
                "last_updated": datetime.utcnow().isoformat()
            }
        }

        return feature_stores.get(model_type, feature_stores[ModelType.READMISSION])


# Global service instance
predictive_engine = PredictiveAnalyticsEngine()
