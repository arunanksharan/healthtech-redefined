"""
Risk Stratification Service Pydantic Schemas
Request/Response models for risk models, versions, predictions, and performance
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Risk Model Schemas ====================

class RiskModelCreate(BaseModel):
    """Schema for creating a risk model"""

    tenant_id: UUID
    code: str = Field(..., description="Unique model code (e.g., READMIT_30D, MORTALITY_ICU, SEPSIS_6H)")
    name: str = Field(..., description="Human-readable model name")
    description: Optional[str] = None
    target_label: str = Field(..., description="What the model predicts (e.g., 30d_readmission, mortality, aki_stage2)")
    prediction_horizon: Optional[str] = Field(None, description="Time horizon (e.g., 24h, 30d, in_hospital)")
    model_type: str = Field(default="classification", description="classification, regression")
    risk_categories: Optional[List[str]] = Field(
        default=["low", "medium", "high", "very_high"],
        description="Risk bucket labels"
    )
    is_active: bool = Field(default=True)

    @validator("model_type")
    def validate_model_type(cls, v):
        valid_types = ["classification", "regression"]
        if v.lower() not in valid_types:
            raise ValueError(f"model_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "code": "READMIT_30D_CARDIO",
                "name": "30-Day Readmission Risk - Cardiology",
                "description": "Predicts all-cause 30-day readmission risk for cardiology patients",
                "target_label": "readmission_30d",
                "prediction_horizon": "30d",
                "model_type": "classification",
                "risk_categories": ["low", "medium", "high", "very_high"]
            }
        }


class RiskModelUpdate(BaseModel):
    """Schema for updating a risk model"""

    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RiskModelResponse(BaseModel):
    """Response schema for risk model"""

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    target_label: str
    prediction_horizon: Optional[str] = None
    model_type: str
    risk_categories: List[str]
    default_version_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RiskModelListResponse(BaseModel):
    """Response for list of risk models"""

    total: int
    models: List[RiskModelResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Risk Model Version Schemas ====================

class RiskModelVersionCreate(BaseModel):
    """Schema for creating a model version"""

    version: str = Field(..., description="Version identifier (e.g., v1.0, 2025-01-15)")
    description: Optional[str] = None
    artifact_location: str = Field(..., description="S3/GCS path to model artifact")
    input_schema: Dict[str, Any] = Field(..., description="Expected input features and types")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output format specification")
    hyperparameters: Optional[Dict[str, Any]] = None
    training_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Training dataset info, framework, metrics"
    )
    risk_thresholds: Optional[Dict[str, float]] = Field(
        None,
        description="Thresholds for risk buckets (e.g., {'low': 0.1, 'medium': 0.3, 'high': 0.6})"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "version": "v1.2",
                "description": "Updated with 2024 Q4 data, improved calibration",
                "artifact_location": "s3://models/readmit_30d_cardio_v1.2.pkl",
                "input_schema": {
                    "age": "float",
                    "prior_admissions": "int",
                    "comorbidity_score": "float",
                    "los_days": "float",
                    "discharge_diagnosis": "string"
                },
                "hyperparameters": {
                    "model": "xgboost",
                    "max_depth": 6,
                    "n_estimators": 100,
                    "learning_rate": 0.1
                },
                "training_metadata": {
                    "train_samples": 5000,
                    "train_period": "2023-01-01 to 2024-12-31",
                    "framework": "xgboost==1.7.0"
                },
                "risk_thresholds": {
                    "low": 0.1,
                    "medium": 0.3,
                    "high": 0.6
                }
            }
        }


class RiskModelVersionUpdate(BaseModel):
    """Schema for updating a model version"""

    description: Optional[str] = None
    is_deprecated: Optional[bool] = None


class RiskModelVersionResponse(BaseModel):
    """Response schema for model version"""

    id: UUID
    risk_model_id: UUID
    version: str
    description: Optional[str] = None
    artifact_location: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    training_metadata: Optional[Dict[str, Any]] = None
    risk_thresholds: Optional[Dict[str, float]] = None
    is_default: bool
    is_deprecated: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RiskModelVersionListResponse(BaseModel):
    """Response for list of model versions"""

    total: int
    versions: List[RiskModelVersionResponse]
    model: RiskModelResponse
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class SetDefaultVersionRequest(BaseModel):
    """Request to set a version as default"""

    pass  # No body needed, version ID comes from path


# ==================== Risk Score Schemas ====================

class RiskScorePredictRequest(BaseModel):
    """Request to generate a risk prediction"""

    tenant_id: UUID
    patient_id: UUID
    episode_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    risk_model_code: str = Field(..., description="Code of risk model to use")
    model_version: Optional[str] = Field(None, description="Specific version, or use default")
    input_features: Dict[str, Any] = Field(..., description="Feature values for prediction")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context (ward, provider, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "patient_id": "patient-uuid-abc123",
                "episode_id": "episode-uuid-xyz789",
                "risk_model_code": "READMIT_30D_CARDIO",
                "input_features": {
                    "age": 67.5,
                    "prior_admissions": 2,
                    "comorbidity_score": 3.2,
                    "los_days": 5.0,
                    "discharge_diagnosis": "I21.9"
                },
                "context": {
                    "ward": "CCU",
                    "discharge_provider": "Dr. Sharma"
                }
            }
        }


class RiskScoreResponse(BaseModel):
    """Response schema for risk score"""

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    episode_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    risk_model_version_id: UUID
    prediction_time: datetime
    predicted_probability: Optional[float] = None
    predicted_value: Optional[float] = None
    risk_bucket: Optional[str] = None
    input_features: Dict[str, Any]
    feature_importance: Optional[Dict[str, float]] = None
    context: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RiskScoreListResponse(BaseModel):
    """Response for list of risk scores"""

    total: int
    scores: List[RiskScoreResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Risk Model Performance Schemas ====================

class EvaluateModelRequest(BaseModel):
    """Request to evaluate model performance"""

    evaluation_period_start: datetime
    evaluation_period_end: datetime
    min_samples: int = Field(default=100, description="Minimum samples required for evaluation")

    class Config:
        json_schema_extra = {
            "example": {
                "evaluation_period_start": "2024-12-01T00:00:00Z",
                "evaluation_period_end": "2025-01-15T23:59:59Z",
                "min_samples": 100
            }
        }


class RiskModelPerformanceResponse(BaseModel):
    """Response schema for model performance metrics"""

    id: UUID
    tenant_id: UUID
    risk_model_version_id: UUID
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    sample_size: int
    auroc: Optional[float] = Field(None, description="Area under ROC curve")
    auprc: Optional[float] = Field(None, description="Area under precision-recall curve")
    calibration_slope: Optional[float] = None
    calibration_intercept: Optional[float] = None
    brier_score: Optional[float] = None
    sensitivity: Optional[float] = None
    specificity: Optional[float] = None
    ppv: Optional[float] = Field(None, description="Positive predictive value")
    npv: Optional[float] = Field(None, description="Negative predictive value")
    drift_score: Optional[float] = Field(None, description="Distribution drift from training")
    metrics_detail: Optional[Dict[str, Any]] = Field(None, description="Additional metrics")
    evaluated_at: datetime

    class Config:
        from_attributes = True


class RiskModelPerformanceListResponse(BaseModel):
    """Response for list of performance evaluations"""

    total: int
    evaluations: List[RiskModelPerformanceResponse]
    version: RiskModelVersionResponse
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
