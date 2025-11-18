"""
Analytics Hub Service
Cohort queries with DSL, data dictionary, and warehouse synchronization

Port: 8017
Endpoints: 3 (Cohort Query, Dictionary, Warehouse Sync)
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import logging
import os
import time

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_, func, desc, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

# Import shared models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from shared.database.models import (
    Base, Episode, Outcome, Patient, Encounter, Admission,
    PROM, PREM, QualityMetric, EventLog
)
from shared.events.publisher import publish_event, EventType

# Import schemas
from schemas import (
    CohortQueryRequest, CohortQueryResponse, CohortQueryResult,
    DataDictionaryResponse, FieldDefinition, CodeSystemDefinition, MetricCatalogEntry,
    WarehouseSyncRequest, WarehouseSyncResponse
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
    title="Analytics Hub Service",
    description="Cohort queries, data dictionary, and warehouse sync for BI tools",
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

def execute_cohort_query_dsl(db: Session, query_request: CohortQueryRequest) -> List[CohortQueryResult]:
    """
    Execute a cohort query using the DSL

    In production, this would:
    - Parse DSL into SQL
    - Execute optimized query
    - Handle complex joins across entities
    - Support all operators and aggregations

    For now, returns simplified implementation
    """
    population = query_request.population
    outcomes_filters = query_request.outcomes or []
    group_by = query_request.group_by or []
    metrics = query_request.metrics
    time_range = query_request.time_range

    # Build base query based on population type
    if population.type == "episode":
        base_query = db.query(Episode).filter(Episode.tenant_id == query_request.tenant_id)

        # Apply population filters
        for filter_def in population.filters:
            field = filter_def.field
            op = filter_def.op
            value = filter_def.value

            if field == "specialty" and op == "=":
                base_query = base_query.filter(Episode.specialty == value)
            elif field == "care_type" and op == "=":
                base_query = base_query.filter(Episode.care_type == value)
            elif field == "status" and op == "=":
                base_query = base_query.filter(Episode.status == value)
            elif field == "started_at" and op == ">=":
                base_query = base_query.filter(Episode.started_at >= value)
            elif field == "started_at" and op == "<=":
                base_query = base_query.filter(Episode.started_at <= value)

        # Apply time range
        if time_range:
            if "start" in time_range:
                base_query = base_query.filter(Episode.started_at >= time_range["start"])
            if "end" in time_range:
                base_query = base_query.filter(Episode.started_at <= time_range["end"])

        # Get episodes
        episodes = base_query.all()

        # If outcome filters, join with outcomes
        if outcomes_filters:
            episode_ids_with_outcomes = set()
            for episode in episodes:
                outcomes = db.query(Outcome).filter(Outcome.episode_id == episode.id).all()
                for outcome in outcomes:
                    # Check outcome filters
                    matches = True
                    for outcome_filter in outcomes_filters:
                        if outcome_filter.field == "outcome_type":
                            if outcome.outcome_type != outcome_filter.value:
                                matches = False
                                break
                    if matches:
                        episode_ids_with_outcomes.add(episode.id)

            # Filter episodes to only those with matching outcomes
            episodes = [e for e in episodes if e.id in episode_ids_with_outcomes]

        # Group and aggregate
        if not group_by:
            # No grouping - single result
            result = calculate_metrics(db, episodes, metrics, query_request)
            return [result]
        else:
            # Group by specified dimensions
            grouped_results = {}
            for episode in episodes:
                # Build group key
                key_parts = []
                dimensions = {}
                for dim in group_by:
                    if dim == "specialty":
                        dimensions["specialty"] = episode.specialty
                        key_parts.append(episode.specialty or "Unknown")
                    elif dim == "month":
                        month = episode.started_at.strftime("%Y-%m") if episode.started_at else "Unknown"
                        dimensions["month"] = month
                        key_parts.append(month)
                    elif dim == "care_type":
                        dimensions["care_type"] = episode.care_type
                        key_parts.append(episode.care_type)

                group_key = tuple(key_parts)
                if group_key not in grouped_results:
                    grouped_results[group_key] = {
                        "dimensions": dimensions,
                        "episodes": []
                    }
                grouped_results[group_key]["episodes"].append(episode)

            # Calculate metrics for each group
            results = []
            for group_key, group_data in grouped_results.items():
                result = calculate_metrics(
                    db,
                    group_data["episodes"],
                    metrics,
                    query_request,
                    group_data["dimensions"]
                )
                results.append(result)

            return results

    else:
        # Other entity types (patient, encounter, etc.) would be implemented similarly
        raise HTTPException(status_code=400, detail=f"Population type '{population.type}' not yet implemented")


def calculate_metrics(
    db: Session,
    episodes: List[Episode],
    metrics: List[Any],
    query_request: CohortQueryRequest,
    dimensions: Optional[Dict[str, Any]] = None
) -> CohortQueryResult:
    """Calculate metrics for a group of episodes"""

    metric_values = {}

    for metric_def in metrics:
        metric_name = metric_def.name or f"{metric_def.type}_metric"

        if metric_def.type == "count":
            metric_values[metric_name] = float(len(episodes))

        elif metric_def.type == "rate":
            # Calculate rate (numerator / denominator)
            # Simplified - would need to count actual outcomes
            numerator = 0
            for episode in episodes:
                outcomes = db.query(Outcome).filter(Outcome.episode_id == episode.id).all()
                # Count outcomes matching criteria
                for outcome in outcomes:
                    if query_request.outcomes:
                        for outcome_filter in query_request.outcomes:
                            if outcome_filter.field == "outcome_type" and outcome.outcome_type == outcome_filter.value:
                                numerator += 1
                                break

            denominator = len(episodes)
            rate = (numerator / denominator * 100) if denominator > 0 else 0.0
            metric_values[metric_name] = round(rate, 2)

        elif metric_def.type == "avg":
            # Calculate average of a field
            # Simplified - would need to extract actual field values
            # Mock: average LOS
            total = sum(
                (episode.ended_at - episode.started_at).days
                if episode.ended_at and episode.started_at
                else 0
                for episode in episodes
            )
            avg_value = total / len(episodes) if len(episodes) > 0 else 0.0
            metric_values[metric_name] = round(avg_value, 2)

        else:
            # Other metric types would be implemented
            metric_values[metric_name] = 0.0

    return CohortQueryResult(
        dimensions=dimensions or {},
        metrics=metric_values,
        sample_size=len(episodes)
    )


def build_data_dictionary() -> DataDictionaryResponse:
    """
    Build comprehensive data dictionary

    In production:
    - Introspect database schema
    - Load code systems from terminology service
    - Include all available metrics

    Returns mock dictionary for now
    """
    fields = [
        FieldDefinition(
            field_name="specialty",
            display_name="Specialty",
            data_type="string",
            entity="episode",
            description="Medical specialty (e.g., CARDIOLOGY, NEUROLOGY)",
            is_filterable=True,
            is_groupable=True,
            valid_operators=["=", "!=", "in", "not_in"]
        ),
        FieldDefinition(
            field_name="care_type",
            display_name="Care Type",
            data_type="string",
            entity="episode",
            description="Type of care (OPD, IPD, DAY_CARE)",
            is_filterable=True,
            is_groupable=True,
            valid_operators=["=", "!=", "in"]
        ),
        FieldDefinition(
            field_name="age",
            display_name="Patient Age",
            data_type="integer",
            entity="patient",
            description="Patient age in years",
            is_filterable=True,
            is_groupable=True,
            valid_operators=["=", "!=", ">", "<", ">=", "<=", "between"]
        ),
        FieldDefinition(
            field_name="started_at",
            display_name="Episode Start",
            data_type="datetime",
            entity="episode",
            description="Episode start date/time",
            is_filterable=True,
            is_groupable=False,
            valid_operators=[">", "<", ">=", "<=", "between"]
        ),
        FieldDefinition(
            field_name="primary_condition_code",
            display_name="Primary Diagnosis",
            data_type="code",
            entity="episode",
            description="Primary condition code (ICD-10 or SNOMED)",
            is_filterable=True,
            is_groupable=True,
            valid_operators=["=", "in", "contains"],
            code_system="ICD-10-CM"
        ),
        FieldDefinition(
            field_name="outcome_type",
            display_name="Outcome Type",
            data_type="string",
            entity="outcome",
            description="Type of outcome (mortality, readmission_30d, complication)",
            is_filterable=True,
            is_groupable=True,
            valid_operators=["=", "in"]
        )
    ]

    code_systems = [
        CodeSystemDefinition(
            code_system="ICD-10-CM",
            version="2025",
            total_codes=72000,
            sample_codes=[
                {"code": "I21.9", "display": "Acute myocardial infarction, unspecified"},
                {"code": "J44.0", "display": "COPD with acute lower respiratory infection"},
                {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"}
            ]
        ),
        CodeSystemDefinition(
            code_system="SNOMED-CT",
            version="2024-09",
            total_codes=350000,
            sample_codes=[
                {"code": "22298006", "display": "Myocardial infarction"},
                {"code": "413839001", "display": "Chronic lung disease"},
                {"code": "44054006", "display": "Diabetes mellitus type 2"}
            ]
        )
    ]

    metrics_catalog = [
        MetricCatalogEntry(
            code="READMIT_30D_RATE",
            name="30-Day Readmission Rate",
            description="All-cause 30-day readmission rate",
            category="effectiveness",
            calculation_type="rate",
            definition_dsl={
                "numerator": {"entity": "outcome", "filters": [{"field": "outcome_type", "op": "=", "value": "readmission_30d"}]},
                "denominator": {"entity": "episode", "filters": [{"field": "status", "op": "=", "value": "completed"}]}
            }
        ),
        MetricCatalogEntry(
            code="AVG_LOS",
            name="Average Length of Stay",
            description="Average length of stay in days",
            category="efficiency",
            calculation_type="avg",
            definition_dsl={
                "type": "avg",
                "field": "los_days",
                "entity": "episode"
            }
        )
    ]

    return DataDictionaryResponse(
        fields=fields,
        code_systems=code_systems,
        metrics_catalog=metrics_catalog,
        entities=["episode", "patient", "encounter", "admission", "appointment", "outcome", "prom", "prem"],
        generated_at=datetime.utcnow()
    )


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "analytics-hub-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Cohort Query Endpoint ====================

@app.post("/api/v1/analytics/cohorts/query", response_model=CohortQueryResponse)
async def execute_cohort_query(
    query_request: CohortQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a cohort query using JSON DSL

    - Define population with filters
    - Link to outcomes
    - Group by dimensions (specialty, month, ward, etc.)
    - Calculate metrics (rates, counts, averages)
    - Returns aggregated results

    **DSL Structure:**
    ```json
    {
      "population": {
        "type": "episode",
        "filters": [{"field": "specialty", "op": "=", "value": "CARDIOLOGY"}]
      },
      "outcomes": [{"field": "outcome_type", "op": "=", "value": "readmission_30d"}],
      "group_by": ["month", "ward"],
      "metrics": [
        {"type": "rate", "numerator": "readmission_count", "denominator": "episode_count"},
        {"type": "avg", "field": "los_days"}
      ]
    }
    ```

    **Use Cases:**
    - Quality dashboards
    - Research cohort identification
    - Performance reports
    - Population health analytics
    """
    try:
        start_time = time.time()
        query_id = str(uuid4())

        logger.info(f"Executing cohort query {query_id} for tenant {query_request.tenant_id}")

        # Execute query
        results = execute_cohort_query_dsl(db, query_request)

        # Apply limit
        if query_request.limit:
            results = results[:query_request.limit]

        execution_time_ms = int((time.time() - start_time) * 1000)

        response = CohortQueryResponse(
            query_id=query_id,
            tenant_id=query_request.tenant_id,
            executed_at=datetime.utcnow(),
            execution_time_ms=execution_time_ms,
            total_results=len(results),
            results=results,
            query_dsl=query_request.dict(),
            warnings=None
        )

        logger.info(f"Cohort query {query_id} completed: {len(results)} results in {execution_time_ms}ms")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing cohort query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Data Dictionary Endpoint ====================

@app.get("/api/v1/analytics/dictionary", response_model=DataDictionaryResponse)
async def get_data_dictionary(
    db: Session = Depends(get_db)
):
    """
    Get comprehensive data dictionary

    Returns:
    - **Fields**: All queryable fields with data types, operators
    - **Code Systems**: Available terminologies (ICD-10, SNOMED, etc.)
    - **Metrics Catalog**: Pre-defined quality metrics
    - **Entities**: Available entity types for queries

    **Use Cases:**
    - BI tool integration (Tableau, PowerBI, Looker)
    - Query builder UIs
    - Report configuration
    - Semantic layer for data exploration
    """
    try:
        dictionary = build_data_dictionary()
        logger.info("Generated data dictionary")
        return dictionary

    except Exception as e:
        logger.error(f"Error building data dictionary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Warehouse Sync Endpoint ====================

@app.post("/api/v1/analytics/sync/trigger", response_model=WarehouseSyncResponse)
async def trigger_warehouse_sync(
    sync_request: WarehouseSyncRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger warehouse synchronization

    - Syncs EMR data to analytics warehouse (Snowflake/BigQuery/Redshift)
    - Processes event log for incremental sync
    - Creates analytics-friendly denormalized tables
    - Ensures EMR-safe aggregations

    **Sync Types:**
    - `full`: Complete data sync (initial load)
    - `incremental`: Only changed records since last sync

    **Workflow:**
    1. Read event log for changes
    2. Extract changed records
    3. Transform to warehouse schema
    4. Load to warehouse tables
    5. Update sync watermark

    **Use Cases:**
    - Daily/hourly warehouse refresh
    - BI dashboard data updates
    - Research data extraction
    - Regulatory reporting
    """
    try:
        sync_job_id = str(uuid4())
        triggered_at = datetime.utcnow()

        logger.info(f"Triggering warehouse sync {sync_job_id} - Type: {sync_request.sync_type}")

        # In production, this would:
        # 1. Queue async job for warehouse sync
        # 2. Process event log to identify changes
        # 3. Extract data in batches
        # 4. Transform and load to warehouse
        # 5. Update sync watermark

        # Mock implementation
        warehouse_location = "snowflake://healthtech_db.analytics/episodes"
        if sync_request.sync_type == "full":
            status = "queued"
            tables_synced = ["episodes", "outcomes", "proms", "prems", "quality_metrics", "risk_scores"]
            records_synced = None  # Will be populated when job completes
        else:
            # Incremental sync
            status = "queued"
            tables_synced = sync_request.tables or ["episodes", "outcomes"]
            records_synced = None

        response = WarehouseSyncResponse(
            sync_job_id=sync_job_id,
            tenant_id=sync_request.tenant_id,
            sync_type=sync_request.sync_type,
            status=status,
            triggered_at=triggered_at,
            started_at=None,  # Will be set when job starts
            completed_at=None,
            tables_synced=tables_synced,
            records_synced=records_synced,
            warehouse_location=warehouse_location,
            errors=None
        )

        logger.info(f"Warehouse sync job {sync_job_id} queued successfully")
        return response

    except Exception as e:
        logger.error(f"Error triggering warehouse sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8017)
