"""
Quality Metrics Service
Manages quality metrics definitions, metric calculations, QI projects, and continuous improvement tracking

Port: 8015
Endpoints: 12 (Metrics CRUD, Metric Values, QI Projects CRUD, QI Project Metrics)
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
import logging
import os

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_, func, desc
from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy.exc import IntegrityError

# Import shared models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from shared.database.models import (
    Base, QualityMetric, QualityMetricValue, QIProject, QIProjectMetric,
    Outcome, Episode, Patient, User
)
from shared.events.publisher import publish_event, EventType

# Import schemas
from schemas import (
    QualityMetricCreate, QualityMetricUpdate, QualityMetricResponse, QualityMetricListResponse,
    QualityMetricValueResponse, QualityMetricValueListResponse, RecalculateRequest, RecalculateResponse,
    QIProjectCreate, QIProjectUpdate, QIProjectResponse, QIProjectListResponse,
    QIProjectMetricCreate, QIProjectMetricResponse, QIProjectMetricListResponse
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
    title="Quality Metrics Service",
    description="Quality metrics, QI projects, and continuous improvement tracking",
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

def calculate_metric_value(db: Session, metric: QualityMetric, period_start: datetime, period_end: datetime) -> dict:
    """
    Calculate metric value for a given period using the metric's definition DSL

    Returns dict with: numerator, denominator, value, calculation_metadata
    """
    try:
        definition = metric.definition_dsl

        # Extract numerator definition
        numerator_def = definition.get("numerator", {})
        denominator_def = definition.get("denominator", {})

        # Calculate numerator
        numerator_value = execute_metric_query(db, numerator_def, period_start, period_end)

        # Calculate denominator
        denominator_value = execute_metric_query(db, denominator_def, period_start, period_end)

        # Calculate final value
        if denominator_value == 0:
            value = 0.0
        else:
            value = (numerator_value / denominator_value) * 100 if metric.unit == "%" else numerator_value / denominator_value

        return {
            "numerator": float(numerator_value),
            "denominator": float(denominator_value),
            "value": round(value, 2),
            "calculation_metadata": {
                "calculation_method": "dsl",
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "definition_version": "1.0"
            }
        }

    except Exception as e:
        logger.error(f"Error calculating metric {metric.code}: {str(e)}")
        raise


def execute_metric_query(db: Session, query_def: dict, period_start: datetime, period_end: datetime) -> int:
    """
    Execute a metric query based on DSL definition

    Simplified implementation - production would have full DSL interpreter
    """
    entity_type = query_def.get("type", "count")
    entity = query_def.get("entity", "episode")
    filters = query_def.get("filters", [])

    # Build base query
    if entity == "episode":
        query = db.query(func.count(Episode.id))
    elif entity == "outcome":
        query = db.query(func.count(Outcome.id))
    else:
        raise ValueError(f"Unsupported entity type: {entity}")

    # Apply time filter
    if entity == "episode":
        query = query.filter(
            and_(
                Episode.started_at >= period_start,
                Episode.started_at < period_end
            )
        )
    elif entity == "outcome":
        query = query.filter(
            and_(
                Outcome.occurred_at >= period_start,
                Outcome.occurred_at < period_end
            )
        )

    # Apply custom filters
    for filter_def in filters:
        field = filter_def.get("field")
        op = filter_def.get("op")
        value = filter_def.get("value")

        # Handle nested fields (e.g., episode.specialty)
        if "." in field:
            # Simplified - would need proper join handling in production
            continue

        # Apply filter based on entity
        if entity == "episode":
            if field == "specialty" and op == "=":
                query = query.filter(Episode.specialty == value)
            elif field == "status" and op == "=":
                query = query.filter(Episode.status == value)
        elif entity == "outcome":
            if field == "outcome_type" and op == "=":
                query = query.filter(Outcome.outcome_type == value)
            elif field == "outcome_subtype" and op == "=":
                query = query.filter(Outcome.outcome_subtype == value)

    # Execute query
    result = query.scalar()
    return result if result else 0


def check_target_met(value: float, target_operator: Optional[str], target_value: Optional[float]) -> Optional[bool]:
    """Check if metric value meets target"""
    if not target_operator or target_value is None:
        return None

    if target_operator == "<":
        return value < target_value
    elif target_operator == "<=":
        return value <= target_value
    elif target_operator == ">":
        return value > target_value
    elif target_operator == ">=":
        return value >= target_value
    elif target_operator == "=":
        return abs(value - target_value) < 0.01  # Float comparison tolerance

    return None


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "quality-metrics-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Quality Metric Endpoints ====================

@app.post("/api/v1/quality/metrics", response_model=QualityMetricResponse, status_code=201)
async def create_quality_metric(
    metric_data: QualityMetricCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new quality metric definition

    - Creates metric with JSON DSL for calculation
    - Validates DSL structure
    - Publishes QUALITY_METRIC_CREATED event
    """
    try:
        # Check if metric code already exists for tenant
        existing = db.query(QualityMetric).filter(
            and_(
                QualityMetric.tenant_id == metric_data.tenant_id,
                QualityMetric.code == metric_data.code
            )
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail=f"Metric with code '{metric_data.code}' already exists")

        # Create quality metric
        metric = QualityMetric(
            tenant_id=metric_data.tenant_id,
            code=metric_data.code,
            name=metric_data.name,
            category=metric_data.category,
            description=metric_data.description,
            definition_dsl=metric_data.definition_dsl,
            unit=metric_data.unit,
            target_operator=metric_data.target_operator,
            target_value=metric_data.target_value,
            calculation_frequency=metric_data.calculation_frequency,
            is_active=metric_data.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        # Publish event
        await publish_event(
            EventType.QUALITY_METRIC_CREATED,
            {
                "metric_id": str(metric.id),
                "tenant_id": str(metric.tenant_id),
                "code": metric.code,
                "name": metric.name,
                "category": metric.category,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Created quality metric: {metric.code} (ID: {metric.id})")
        return metric

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating quality metric: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/quality/metrics", response_model=QualityMetricListResponse)
async def list_quality_metrics(
    tenant_id: Optional[UUID] = Query(None),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List quality metrics with filtering and pagination

    - Filter by tenant, category, active status
    - Paginated results
    - Ordered by created_at descending
    """
    try:
        # Build base query
        query = db.query(QualityMetric)

        # Apply filters
        if tenant_id:
            query = query.filter(QualityMetric.tenant_id == tenant_id)
        if category:
            query = query.filter(QualityMetric.category == category.lower())
        if is_active is not None:
            query = query.filter(QualityMetric.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        metrics = query.order_by(desc(QualityMetric.created_at)).offset(offset).limit(page_size).all()

        return QualityMetricListResponse(
            total=total,
            metrics=metrics,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error(f"Error listing quality metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/quality/metrics/{metric_id}", response_model=QualityMetricResponse)
async def get_quality_metric(
    metric_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific quality metric by ID

    - Returns full metric definition including DSL
    """
    try:
        metric = db.query(QualityMetric).filter(QualityMetric.id == metric_id).first()

        if not metric:
            raise HTTPException(status_code=404, detail="Quality metric not found")

        return metric

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quality metric: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/quality/metrics/{metric_id}", response_model=QualityMetricResponse)
async def update_quality_metric(
    metric_id: UUID,
    metric_update: QualityMetricUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a quality metric

    - Can update name, description, DSL, targets, frequency
    - Cannot update code or tenant_id
    - Publishes QUALITY_METRIC_UPDATED event
    """
    try:
        metric = db.query(QualityMetric).filter(QualityMetric.id == metric_id).first()

        if not metric:
            raise HTTPException(status_code=404, detail="Quality metric not found")

        # Update fields
        update_data = metric_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(metric, field, value)

        metric.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(metric)

        # Publish event
        await publish_event(
            EventType.QUALITY_METRIC_UPDATED,
            {
                "metric_id": str(metric.id),
                "tenant_id": str(metric.tenant_id),
                "code": metric.code,
                "updated_fields": list(update_data.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Updated quality metric: {metric.code} (ID: {metric.id})")
        return metric

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating quality metric: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Metric Value Endpoints ====================

@app.post("/api/v1/quality/metrics/{metric_id}/recalculate", response_model=RecalculateResponse)
async def recalculate_metric(
    metric_id: UUID,
    recalc_request: RecalculateRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger recalculation of metric values for a time period

    - Calculates metric using DSL for each period
    - Creates or updates QualityMetricValue records
    - Publishes QUALITY_METRIC_RECALCULATED event
    """
    try:
        started_at = datetime.utcnow()

        # Get metric
        metric = db.query(QualityMetric).filter(QualityMetric.id == metric_id).first()
        if not metric:
            raise HTTPException(status_code=404, detail="Quality metric not found")

        # Determine calculation periods
        period_start = recalc_request.period_start or (datetime.utcnow() - timedelta(days=30))
        period_end = recalc_request.period_end or datetime.utcnow()

        # Generate periods based on calculation frequency
        periods = []
        current = period_start

        if metric.calculation_frequency == "daily":
            delta = timedelta(days=1)
        elif metric.calculation_frequency == "weekly":
            delta = timedelta(weeks=1)
        elif metric.calculation_frequency == "monthly":
            delta = timedelta(days=30)  # Simplified
        else:
            delta = timedelta(days=1)

        while current < period_end:
            period_end_time = min(current + delta, period_end)
            periods.append((current, period_end_time))
            current = period_end_time

        values_created = 0
        values_updated = 0
        errors = []

        # Calculate for each period
        for p_start, p_end in periods:
            try:
                # Check if value already exists
                existing_value = db.query(QualityMetricValue).filter(
                    and_(
                        QualityMetricValue.quality_metric_id == metric_id,
                        QualityMetricValue.period_start == p_start,
                        QualityMetricValue.period_end == p_end
                    )
                ).first()

                if existing_value and not recalc_request.force:
                    continue  # Skip if exists and not forcing

                # Calculate metric value
                calc_result = calculate_metric_value(db, metric, p_start, p_end)

                # Check if target met
                meets_target = check_target_met(
                    calc_result["value"],
                    metric.target_operator,
                    metric.target_value
                )

                if existing_value:
                    # Update existing
                    existing_value.numerator = calc_result["numerator"]
                    existing_value.denominator = calc_result["denominator"]
                    existing_value.value = calc_result["value"]
                    existing_value.meets_target = meets_target
                    existing_value.calculation_metadata = calc_result["calculation_metadata"]
                    existing_value.calculated_at = datetime.utcnow()
                    values_updated += 1
                else:
                    # Create new
                    new_value = QualityMetricValue(
                        tenant_id=metric.tenant_id,
                        quality_metric_id=metric_id,
                        period_start=p_start,
                        period_end=p_end,
                        numerator=calc_result["numerator"],
                        denominator=calc_result["denominator"],
                        value=calc_result["value"],
                        meets_target=meets_target,
                        calculation_metadata=calc_result["calculation_metadata"],
                        calculated_at=datetime.utcnow()
                    )
                    db.add(new_value)
                    values_created += 1

            except Exception as e:
                errors.append(f"Period {p_start.isoformat()}: {str(e)}")
                logger.error(f"Error calculating period {p_start}: {str(e)}")

        db.commit()
        completed_at = datetime.utcnow()

        # Publish event
        await publish_event(
            EventType.QUALITY_METRIC_RECALCULATED,
            {
                "metric_id": str(metric.id),
                "tenant_id": str(metric.tenant_id),
                "code": metric.code,
                "periods_calculated": len(periods),
                "values_created": values_created,
                "values_updated": values_updated,
                "timestamp": completed_at.isoformat()
            }
        )

        logger.info(f"Recalculated metric {metric.code}: {values_created} created, {values_updated} updated")

        return RecalculateResponse(
            quality_metric_id=metric_id,
            periods_calculated=len(periods),
            values_created=values_created,
            values_updated=values_updated,
            started_at=started_at,
            completed_at=completed_at,
            errors=errors if errors else None
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error recalculating metric: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/quality/metrics/{metric_id}/values", response_model=QualityMetricValueListResponse)
async def get_metric_values(
    metric_id: UUID,
    period_start: Optional[datetime] = Query(None),
    period_end: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get time-series values for a quality metric

    - Returns calculated metric values over time
    - Supports time range filtering
    - Ordered by period_start descending (newest first)
    """
    try:
        # Get metric
        metric = db.query(QualityMetric).filter(QualityMetric.id == metric_id).first()
        if not metric:
            raise HTTPException(status_code=404, detail="Quality metric not found")

        # Build query
        query = db.query(QualityMetricValue).filter(QualityMetricValue.quality_metric_id == metric_id)

        # Apply time filters
        if period_start:
            query = query.filter(QualityMetricValue.period_start >= period_start)
        if period_end:
            query = query.filter(QualityMetricValue.period_end <= period_end)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        values = query.order_by(desc(QualityMetricValue.period_start)).offset(offset).limit(page_size).all()

        return QualityMetricValueListResponse(
            total=total,
            values=values,
            metric=metric,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metric values: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== QI Project Endpoints ====================

@app.post("/api/v1/quality/qi-projects", response_model=QIProjectResponse, status_code=201)
async def create_qi_project(
    project_data: QIProjectCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new QI (Quality Improvement) project

    - Creates project with team, timeline, baseline
    - Publishes QI_PROJECT_CREATED event
    """
    try:
        # Validate owner exists if provided
        if project_data.owner_id:
            owner = db.query(User).filter(User.id == project_data.owner_id).first()
            if not owner:
                raise HTTPException(status_code=404, detail="Project owner not found")

        # Create QI project
        project = QIProject(
            tenant_id=project_data.tenant_id,
            title=project_data.title,
            description=project_data.description,
            category=project_data.category,
            status=project_data.status,
            owner_id=project_data.owner_id,
            team_members=project_data.team_members,
            target_start_date=project_data.target_start_date,
            target_end_date=project_data.target_end_date,
            baseline_start=project_data.baseline_start,
            baseline_end=project_data.baseline_end,
            intervention_description=project_data.intervention_description,
            success_criteria=project_data.success_criteria,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        # Publish event
        await publish_event(
            EventType.QI_PROJECT_CREATED,
            {
                "project_id": str(project.id),
                "tenant_id": str(project.tenant_id),
                "title": project.title,
                "category": project.category,
                "status": project.status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Created QI project: {project.title} (ID: {project.id})")
        return project

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating QI project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/quality/qi-projects", response_model=QIProjectListResponse)
async def list_qi_projects(
    tenant_id: Optional[UUID] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    owner_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List QI projects with filtering and pagination

    - Filter by tenant, category, status, owner
    - Paginated results
    - Ordered by created_at descending
    """
    try:
        # Build base query
        query = db.query(QIProject)

        # Apply filters
        if tenant_id:
            query = query.filter(QIProject.tenant_id == tenant_id)
        if category:
            query = query.filter(QIProject.category == category.lower())
        if status:
            query = query.filter(QIProject.status == status.lower())
        if owner_id:
            query = query.filter(QIProject.owner_id == owner_id)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        projects = query.order_by(desc(QIProject.created_at)).offset(offset).limit(page_size).all()

        return QIProjectListResponse(
            total=total,
            projects=projects,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error(f"Error listing QI projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/quality/qi-projects/{project_id}", response_model=QIProjectResponse)
async def get_qi_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific QI project by ID

    - Returns full project details
    """
    try:
        project = db.query(QIProject).filter(QIProject.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="QI project not found")

        return project

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching QI project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/quality/qi-projects/{project_id}", response_model=QIProjectResponse)
async def update_qi_project(
    project_id: UUID,
    project_update: QIProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a QI project

    - Can update status, team, timeline, results
    - Publishes QI_PROJECT_UPDATED or QI_PROJECT_COMPLETED event
    """
    try:
        project = db.query(QIProject).filter(QIProject.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="QI project not found")

        # Track status change
        old_status = project.status

        # Update fields
        update_data = project_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        project.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(project)

        # Publish appropriate event
        if project.status == "completed" and old_status != "completed":
            event_type = EventType.QI_PROJECT_COMPLETED
        else:
            event_type = EventType.QI_PROJECT_UPDATED

        await publish_event(
            event_type,
            {
                "project_id": str(project.id),
                "tenant_id": str(project.tenant_id),
                "title": project.title,
                "status": project.status,
                "old_status": old_status,
                "updated_fields": list(update_data.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Updated QI project: {project.title} (ID: {project.id})")
        return project

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating QI project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== QI Project Metric Endpoints ====================

@app.post("/api/v1/quality/qi-projects/{project_id}/metrics", response_model=QIProjectMetricResponse, status_code=201)
async def link_metric_to_project(
    project_id: UUID,
    metric_link: QIProjectMetricCreate,
    db: Session = Depends(get_db)
):
    """
    Link a quality metric to a QI project

    - Associates metric with project
    - Sets baseline and target values
    - Can designate primary outcome metric
    """
    try:
        # Validate project exists
        project = db.query(QIProject).filter(QIProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="QI project not found")

        # Validate metric exists
        metric = db.query(QualityMetric).filter(QualityMetric.id == metric_link.quality_metric_id).first()
        if not metric:
            raise HTTPException(status_code=404, detail="Quality metric not found")

        # Check if already linked
        existing = db.query(QIProjectMetric).filter(
            and_(
                QIProjectMetric.qi_project_id == project_id,
                QIProjectMetric.quality_metric_id == metric_link.quality_metric_id
            )
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Metric already linked to this project")

        # Create link
        project_metric = QIProjectMetric(
            qi_project_id=project_id,
            quality_metric_id=metric_link.quality_metric_id,
            is_primary=metric_link.is_primary,
            baseline_value=metric_link.baseline_value,
            target_value=metric_link.target_value,
            notes=metric_link.notes,
            created_at=datetime.utcnow()
        )

        db.add(project_metric)
        db.commit()
        db.refresh(project_metric)

        # Load metric relationship
        db.refresh(project_metric)
        project_metric.metric = metric

        logger.info(f"Linked metric {metric.code} to project {project.title}")
        return project_metric

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking metric to project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/quality/qi-projects/{project_id}/metrics", response_model=QIProjectMetricListResponse)
async def list_project_metrics(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all metrics linked to a QI project

    - Returns metrics with baseline, target, current values
    - Includes full metric definitions
    - Primary metrics listed first
    """
    try:
        # Validate project exists
        project = db.query(QIProject).filter(QIProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="QI project not found")

        # Build query with metric join
        query = db.query(QIProjectMetric).filter(
            QIProjectMetric.qi_project_id == project_id
        ).options(joinedload(QIProjectMetric.metric))

        # Get total count
        total = query.count()

        # Apply pagination - primary metrics first
        offset = (page - 1) * page_size
        project_metrics = query.order_by(
            desc(QIProjectMetric.is_primary),
            QIProjectMetric.created_at
        ).offset(offset).limit(page_size).all()

        return QIProjectMetricListResponse(
            total=total,
            project_metrics=project_metrics,
            project=project,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing project metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)
