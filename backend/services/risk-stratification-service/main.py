"""
Risk Stratification Service
ML model registry, versioning, risk predictions, and performance tracking

Port: 8016
Endpoints: 13 (Models CRUD, Model Versions, Inference, Performance Tracking)
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import os
import json

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_, func, desc
from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy.exc import IntegrityError

# Import shared models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from shared.database.models import (
    Base, RiskModel, RiskModelVersion, RiskScore, RiskModelPerformance,
    Patient, Episode, Outcome, User
)
from shared.events.publisher import publish_event, EventType

# Import schemas
from schemas import (
    RiskModelCreate, RiskModelUpdate, RiskModelResponse, RiskModelListResponse,
    RiskModelVersionCreate, RiskModelVersionUpdate, RiskModelVersionResponse, RiskModelVersionListResponse,
    SetDefaultVersionRequest,
    RiskScorePredictRequest, RiskScoreResponse, RiskScoreListResponse,
    EvaluateModelRequest, RiskModelPerformanceResponse, RiskModelPerformanceListResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://healthtech:healthtech123@localhost:5432/healthtech_db"
)
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Risk Stratification Service",
    description="ML model registry, versioning, risk predictions, and performance tracking",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# Dependencies
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== Helper Functions ====================

def load_model_and_predict(
    model_version: RiskModelVersion,
    input_features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Load ML model from artifact location and generate prediction

    In production, this would:
    - Load model from S3/GCS
    - Validate input features against schema
    - Run inference
    - Calculate feature importance (SHAP values)

    For now, returns mock prediction
    """
    # TODO: Implement actual model loading and inference
    # This is a placeholder implementation

    # Mock prediction based on feature values
    predicted_prob = 0.35  # Mock probability

    # Determine risk bucket based on thresholds
    risk_bucket = "low"
    if model_version.risk_thresholds:
        thresholds = model_version.risk_thresholds
        if predicted_prob >= thresholds.get("high", 0.6):
            risk_bucket = "very_high"
        elif predicted_prob >= thresholds.get("medium", 0.3):
            risk_bucket = "high"
        elif predicted_prob >= thresholds.get("low", 0.1):
            risk_bucket = "medium"

    # Mock feature importance
    feature_importance = {
        feature: round(0.1 + (hash(feature) % 20) / 100, 3)
        for feature in input_features.keys()
    }

    return {
        "predicted_probability": predicted_prob,
        "risk_bucket": risk_bucket,
        "feature_importance": feature_importance
    }


def calculate_model_performance(
    db: Session,
    model_version: RiskModelVersion,
    period_start: datetime,
    period_end: datetime
) -> Dict[str, Any]:
    """
    Calculate model performance metrics by comparing predictions to outcomes

    In production:
    - Fetch all predictions in period
    - Match to actual outcomes
    - Calculate AUROC, calibration, etc.

    For now, returns mock metrics
    """
    # Get predictions in period
    predictions = db.query(RiskScore).filter(
        and_(
            RiskScore.risk_model_version_id == model_version.id,
            RiskScore.prediction_time >= period_start,
            RiskScore.prediction_time < period_end
        )
    ).all()

    sample_size = len(predictions)

    if sample_size == 0:
        raise ValueError("No predictions found in evaluation period")

    # TODO: Implement actual performance calculation
    # This is a placeholder with mock metrics

    metrics = {
        "sample_size": sample_size,
        "auroc": 0.78,
        "auprc": 0.65,
        "calibration_slope": 0.95,
        "calibration_intercept": 0.02,
        "brier_score": 0.15,
        "sensitivity": 0.72,
        "specificity": 0.81,
        "ppv": 0.68,
        "npv": 0.84,
        "drift_score": 0.03,
        "metrics_detail": {
            "confusion_matrix": {
                "tp": int(sample_size * 0.2),
                "fp": int(sample_size * 0.1),
                "tn": int(sample_size * 0.6),
                "fn": int(sample_size * 0.1)
            },
            "roc_curve": "stored_separately",
            "calibration_curve": "stored_separately"
        }
    }

    return metrics


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "risk-stratification-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Risk Model Endpoints ====================

@app.post("/api/v1/risk/models", response_model=RiskModelResponse, status_code=201)
async def create_risk_model(
    model_data: RiskModelCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new risk model

    - Creates model definition
    - No versions yet (add via /models/{id}/versions)
    - Publishes RISK_MODEL_CREATED event
    """
    try:
        # Check if model code already exists for tenant
        existing = db.query(RiskModel).filter(
            and_(
                RiskModel.tenant_id == model_data.tenant_id,
                RiskModel.code == model_data.code
            )
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail=f"Model with code '{model_data.code}' already exists")

        # Create risk model
        model = RiskModel(
            tenant_id=model_data.tenant_id,
            code=model_data.code,
            name=model_data.name,
            description=model_data.description,
            target_label=model_data.target_label,
            prediction_horizon=model_data.prediction_horizon,
            model_type=model_data.model_type,
            risk_categories=model_data.risk_categories,
            is_active=model_data.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        # Publish event
        await publish_event(
            EventType.RISK_MODEL_CREATED,
            {
                "model_id": str(model.id),
                "tenant_id": str(model.tenant_id),
                "code": model.code,
                "name": model.name,
                "target_label": model.target_label,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Created risk model: {model.code} (ID: {model.id})")
        return model

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating risk model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/risk/models", response_model=RiskModelListResponse)
async def list_risk_models(
    tenant_id: Optional[UUID] = Query(None),
    model_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List risk models with filtering and pagination

    - Filter by tenant, model_type, active status
    - Paginated results
    - Ordered by created_at descending
    """
    try:
        # Build base query
        query = db.query(RiskModel)

        # Apply filters
        if tenant_id:
            query = query.filter(RiskModel.tenant_id == tenant_id)
        if model_type:
            query = query.filter(RiskModel.model_type == model_type.lower())
        if is_active is not None:
            query = query.filter(RiskModel.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        models = query.order_by(desc(RiskModel.created_at)).offset(offset).limit(page_size).all()

        return RiskModelListResponse(
            total=total,
            models=models,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error(f"Error listing risk models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/risk/models/{model_id}", response_model=RiskModelResponse)
async def get_risk_model(
    model_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific risk model by ID

    - Returns full model definition
    """
    try:
        model = db.query(RiskModel).filter(RiskModel.id == model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="Risk model not found")

        return model

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risk model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/risk/models/{model_id}", response_model=RiskModelResponse)
async def update_risk_model(
    model_id: UUID,
    model_update: RiskModelUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a risk model

    - Can update name, description, active status
    - Cannot change code or model_type
    """
    try:
        model = db.query(RiskModel).filter(RiskModel.id == model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="Risk model not found")

        # Update fields
        update_data = model_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(model, field, value)

        model.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(model)

        logger.info(f"Updated risk model: {model.code} (ID: {model.id})")
        return model

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating risk model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Risk Model Version Endpoints ====================

@app.post("/api/v1/risk/models/{model_id}/versions", response_model=RiskModelVersionResponse, status_code=201)
async def create_model_version(
    model_id: UUID,
    version_data: RiskModelVersionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new version of a risk model

    - Adds versioned model artifact
    - Can set as default if it's the first version
    - Publishes RISK_MODEL_VERSION_CREATED event
    """
    try:
        # Validate model exists
        model = db.query(RiskModel).filter(RiskModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Risk model not found")

        # Check if version already exists
        existing = db.query(RiskModelVersion).filter(
            and_(
                RiskModelVersion.risk_model_id == model_id,
                RiskModelVersion.version == version_data.version
            )
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail=f"Version '{version_data.version}' already exists")

        # Check if this is the first version
        version_count = db.query(RiskModelVersion).filter(
            RiskModelVersion.risk_model_id == model_id
        ).count()
        is_first = version_count == 0

        # Create model version
        model_version = RiskModelVersion(
            risk_model_id=model_id,
            version=version_data.version,
            description=version_data.description,
            artifact_location=version_data.artifact_location,
            input_schema=version_data.input_schema,
            output_schema=version_data.output_schema,
            hyperparameters=version_data.hyperparameters,
            training_metadata=version_data.training_metadata,
            risk_thresholds=version_data.risk_thresholds,
            is_default=is_first,  # First version becomes default
            is_deprecated=False,
            created_at=datetime.utcnow()
        )

        db.add(model_version)
        db.flush()

        # If first version, update model's default_version_id
        if is_first:
            model.default_version_id = model_version.id

        db.commit()
        db.refresh(model_version)

        logger.info(f"Created model version {version_data.version} for {model.code} (ID: {model_version.id})")
        return model_version

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating model version: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/risk/models/{model_id}/versions", response_model=RiskModelVersionListResponse)
async def list_model_versions(
    model_id: UUID,
    include_deprecated: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all versions of a risk model

    - Returns versions with metadata
    - Can exclude deprecated versions
    - Default version listed first
    """
    try:
        # Validate model exists
        model = db.query(RiskModel).filter(RiskModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Risk model not found")

        # Build query
        query = db.query(RiskModelVersion).filter(RiskModelVersion.risk_model_id == model_id)

        # Filter deprecated
        if not include_deprecated:
            query = query.filter(RiskModelVersion.is_deprecated == False)

        # Get total count
        total = query.count()

        # Apply pagination - default first
        offset = (page - 1) * page_size
        versions = query.order_by(
            desc(RiskModelVersion.is_default),
            desc(RiskModelVersion.created_at)
        ).offset(offset).limit(page_size).all()

        return RiskModelVersionListResponse(
            total=total,
            versions=versions,
            model=model,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing model versions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/risk/model-versions/{version_id}", response_model=RiskModelVersionResponse)
async def update_model_version(
    version_id: UUID,
    version_update: RiskModelVersionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a model version

    - Can update description, deprecation status
    - Cannot change version number or artifact
    """
    try:
        version = db.query(RiskModelVersion).filter(RiskModelVersion.id == version_id).first()

        if not version:
            raise HTTPException(status_code=404, detail="Model version not found")

        # Update fields
        update_data = version_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(version, field, value)

        db.commit()
        db.refresh(version)

        # If deprecating the default version, warn
        if version.is_deprecated and version.is_default:
            logger.warning(f"Deprecated version {version.version} is still set as default!")

        logger.info(f"Updated model version {version.version} (ID: {version.id})")
        return version

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating model version: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/risk/model-versions/{version_id}/set-default", response_model=RiskModelVersionResponse)
async def set_default_version(
    version_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Set a version as the default for its model

    - Unsets previous default
    - Publishes RISK_MODEL_VERSION_ACTIVATED event
    """
    try:
        # Get the version
        version = db.query(RiskModelVersion).filter(RiskModelVersion.id == version_id).first()
        if not version:
            raise HTTPException(status_code=404, detail="Model version not found")

        if version.is_deprecated:
            raise HTTPException(status_code=400, detail="Cannot set deprecated version as default")

        # Get the model
        model = db.query(RiskModel).filter(RiskModel.id == version.risk_model_id).first()

        # Unset current default
        if model.default_version_id:
            current_default = db.query(RiskModelVersion).filter(
                RiskModelVersion.id == model.default_version_id
            ).first()
            if current_default:
                current_default.is_default = False

        # Set new default
        version.is_default = True
        model.default_version_id = version.id

        db.commit()
        db.refresh(version)

        # Publish event
        await publish_event(
            EventType.RISK_MODEL_VERSION_ACTIVATED,
            {
                "version_id": str(version.id),
                "model_id": str(model.id),
                "tenant_id": str(model.tenant_id),
                "code": model.code,
                "version": version.version,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Set version {version.version} as default for model {model.code}")
        return version

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting default version: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Risk Score / Inference Endpoints ====================

@app.post("/api/v1/risk/scores/predict", response_model=RiskScoreResponse, status_code=201)
async def predict_risk_score(
    predict_request: RiskScorePredictRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a risk prediction

    - Loads specified model version (or default)
    - Runs inference with input features
    - Stores prediction with feature importance
    - Publishes RISK_SCORE_CREATED event
    """
    try:
        # Validate patient exists
        patient = db.query(Patient).filter(Patient.id == predict_request.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Get risk model
        model = db.query(RiskModel).filter(
            and_(
                RiskModel.tenant_id == predict_request.tenant_id,
                RiskModel.code == predict_request.risk_model_code
            )
        ).first()

        if not model:
            raise HTTPException(status_code=404, detail=f"Risk model '{predict_request.risk_model_code}' not found")

        # Get model version
        if predict_request.model_version:
            # Use specified version
            model_version = db.query(RiskModelVersion).filter(
                and_(
                    RiskModelVersion.risk_model_id == model.id,
                    RiskModelVersion.version == predict_request.model_version
                )
            ).first()
        else:
            # Use default version
            if not model.default_version_id:
                raise HTTPException(status_code=400, detail="No default model version set")
            model_version = db.query(RiskModelVersion).filter(
                RiskModelVersion.id == model.default_version_id
            ).first()

        if not model_version:
            raise HTTPException(status_code=404, detail="Model version not found")

        if model_version.is_deprecated:
            logger.warning(f"Using deprecated model version {model_version.version}")

        # Run prediction
        prediction_result = load_model_and_predict(model_version, predict_request.input_features)

        # Create risk score record
        risk_score = RiskScore(
            tenant_id=predict_request.tenant_id,
            patient_id=predict_request.patient_id,
            episode_id=predict_request.episode_id,
            encounter_id=predict_request.encounter_id,
            risk_model_version_id=model_version.id,
            prediction_time=datetime.utcnow(),
            predicted_probability=prediction_result.get("predicted_probability"),
            risk_bucket=prediction_result.get("risk_bucket"),
            input_features=predict_request.input_features,
            feature_importance=prediction_result.get("feature_importance"),
            context=predict_request.context,
            created_at=datetime.utcnow()
        )

        db.add(risk_score)
        db.commit()
        db.refresh(risk_score)

        # Publish event
        await publish_event(
            EventType.RISK_SCORE_CREATED,
            {
                "score_id": str(risk_score.id),
                "tenant_id": str(risk_score.tenant_id),
                "patient_id": str(risk_score.patient_id),
                "model_code": model.code,
                "model_version": model_version.version,
                "risk_bucket": risk_score.risk_bucket,
                "predicted_probability": risk_score.predicted_probability,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Generated risk prediction for patient {patient.id}: {risk_score.risk_bucket}")
        return risk_score

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating risk prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/risk/scores", response_model=RiskScoreListResponse)
async def list_risk_scores(
    tenant_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    episode_id: Optional[UUID] = Query(None),
    risk_bucket: Optional[str] = Query(None),
    prediction_time_start: Optional[datetime] = Query(None),
    prediction_time_end: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    List risk scores with filtering and pagination

    - Filter by tenant, patient, episode, risk bucket, time range
    - Paginated results
    - Ordered by prediction_time descending
    """
    try:
        # Build base query
        query = db.query(RiskScore)

        # Apply filters
        if tenant_id:
            query = query.filter(RiskScore.tenant_id == tenant_id)
        if patient_id:
            query = query.filter(RiskScore.patient_id == patient_id)
        if episode_id:
            query = query.filter(RiskScore.episode_id == episode_id)
        if risk_bucket:
            query = query.filter(RiskScore.risk_bucket == risk_bucket)
        if prediction_time_start:
            query = query.filter(RiskScore.prediction_time >= prediction_time_start)
        if prediction_time_end:
            query = query.filter(RiskScore.prediction_time <= prediction_time_end)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        scores = query.order_by(desc(RiskScore.prediction_time)).offset(offset).limit(page_size).all()

        return RiskScoreListResponse(
            total=total,
            scores=scores,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error(f"Error listing risk scores: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Model Performance Endpoints ====================

@app.post("/api/v1/risk/model-versions/{version_id}/evaluate", response_model=RiskModelPerformanceResponse)
async def evaluate_model_performance(
    version_id: UUID,
    eval_request: EvaluateModelRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate model performance for a time period

    - Compares predictions to actual outcomes
    - Calculates AUROC, calibration, drift
    - Stores performance metrics
    - Publishes RISK_MODEL_PERFORMANCE_UPDATED event
    """
    try:
        # Get model version
        model_version = db.query(RiskModelVersion).filter(RiskModelVersion.id == version_id).first()
        if not model_version:
            raise HTTPException(status_code=404, detail="Model version not found")

        # Get model
        model = db.query(RiskModel).filter(RiskModel.id == model_version.risk_model_id).first()

        # Calculate performance metrics
        metrics = calculate_model_performance(
            db,
            model_version,
            eval_request.evaluation_period_start,
            eval_request.evaluation_period_end
        )

        if metrics["sample_size"] < eval_request.min_samples:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient samples: {metrics['sample_size']} < {eval_request.min_samples}"
            )

        # Create performance record
        performance = RiskModelPerformance(
            tenant_id=model.tenant_id,
            risk_model_version_id=version_id,
            evaluation_period_start=eval_request.evaluation_period_start,
            evaluation_period_end=eval_request.evaluation_period_end,
            sample_size=metrics["sample_size"],
            auroc=metrics.get("auroc"),
            auprc=metrics.get("auprc"),
            calibration_slope=metrics.get("calibration_slope"),
            calibration_intercept=metrics.get("calibration_intercept"),
            brier_score=metrics.get("brier_score"),
            sensitivity=metrics.get("sensitivity"),
            specificity=metrics.get("specificity"),
            ppv=metrics.get("ppv"),
            npv=metrics.get("npv"),
            drift_score=metrics.get("drift_score"),
            metrics_detail=metrics.get("metrics_detail"),
            evaluated_at=datetime.utcnow()
        )

        db.add(performance)
        db.commit()
        db.refresh(performance)

        # Publish event
        await publish_event(
            EventType.RISK_MODEL_PERFORMANCE_UPDATED,
            {
                "performance_id": str(performance.id),
                "version_id": str(version_id),
                "model_id": str(model.id),
                "tenant_id": str(model.tenant_id),
                "auroc": performance.auroc,
                "sample_size": performance.sample_size,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Evaluated model version {model_version.version}: AUROC {performance.auroc}")
        return performance

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error evaluating model performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/risk/model-versions/{version_id}/performance", response_model=RiskModelPerformanceListResponse)
async def get_model_performance_history(
    version_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get performance evaluation history for a model version

    - Returns all evaluations over time
    - Ordered by evaluation date descending
    - Useful for monitoring drift and degradation
    """
    try:
        # Get model version
        model_version = db.query(RiskModelVersion).filter(RiskModelVersion.id == version_id).first()
        if not model_version:
            raise HTTPException(status_code=404, detail="Model version not found")

        # Build query
        query = db.query(RiskModelPerformance).filter(
            RiskModelPerformance.risk_model_version_id == version_id
        )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        evaluations = query.order_by(desc(RiskModelPerformance.evaluated_at)).offset(offset).limit(page_size).all()

        return RiskModelPerformanceListResponse(
            total=total,
            evaluations=evaluations,
            version=model_version,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching performance history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8016)
