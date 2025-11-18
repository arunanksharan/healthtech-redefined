"""
Analytics Hub Service Pydantic Schemas
Request/Response models for cohort queries, dictionary, and warehouse sync
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Cohort Query Schemas ====================

class CohortFilter(BaseModel):
    """A single filter condition"""

    field: str = Field(..., description="Field name (e.g., 'specialty', 'age', 'diagnosis_code')")
    op: str = Field(..., description="Operator: =, !=, >, <, >=, <=, in, not_in, contains, between")
    value: Union[str, int, float, List[Any]] = Field(..., description="Filter value(s)")

    @validator("op")
    def validate_operator(cls, v):
        valid_ops = ["=", "!=", ">", "<", ">=", "<=", "in", "not_in", "contains", "between"]
        if v not in valid_ops:
            raise ValueError(f"op must be one of: {', '.join(valid_ops)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "field": "specialty",
                "op": "=",
                "value": "CARDIOLOGY"
            }
        }


class PopulationDefinition(BaseModel):
    """Defines the population for the cohort"""

    type: str = Field(..., description="Entity type: episode, patient, encounter, admission")
    filters: List[CohortFilter] = Field(default_factory=list, description="Population filters")

    @validator("type")
    def validate_type(cls, v):
        valid_types = ["episode", "patient", "encounter", "admission", "appointment"]
        if v.lower() not in valid_types:
            raise ValueError(f"type must be one of: {', '.join(valid_types)}")
        return v.lower()


class MetricDefinition(BaseModel):
    """Defines a metric to calculate"""

    type: str = Field(..., description="rate, count, avg, median, sum, min, max, percentile")
    name: Optional[str] = Field(None, description="Metric name (auto-generated if not provided)")
    numerator: Optional[str] = Field(None, description="Numerator field (for rate metrics)")
    denominator: Optional[str] = Field(None, description="Denominator field (for rate metrics)")
    field: Optional[str] = Field(None, description="Field to aggregate (for avg, sum, etc.)")
    percentile: Optional[float] = Field(None, description="Percentile value (for percentile metrics)")

    @validator("type")
    def validate_type(cls, v):
        valid_types = ["rate", "count", "avg", "median", "sum", "min", "max", "percentile"]
        if v.lower() not in valid_types:
            raise ValueError(f"type must be one of: {', '.join(valid_types)}")
        return v.lower()


class CohortQueryRequest(BaseModel):
    """Request to execute a cohort query"""

    tenant_id: UUID
    population: PopulationDefinition = Field(..., description="Population definition")
    outcomes: Optional[List[CohortFilter]] = Field(default_factory=list, description="Outcome filters")
    group_by: Optional[List[str]] = Field(default_factory=list, description="Grouping dimensions")
    metrics: List[MetricDefinition] = Field(..., description="Metrics to calculate")
    time_range: Optional[Dict[str, datetime]] = Field(
        None,
        description="Time range filter {'start': datetime, 'end': datetime}"
    )
    limit: Optional[int] = Field(None, ge=1, le=10000, description="Result limit")

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "population": {
                    "type": "episode",
                    "filters": [
                        {"field": "specialty", "op": "=", "value": "CARDIOLOGY"},
                        {"field": "started_at", "op": ">=", "value": "2025-01-01"}
                    ]
                },
                "outcomes": [
                    {"field": "outcome_type", "op": "=", "value": "readmission_30d"}
                ],
                "group_by": ["month", "ward"],
                "metrics": [
                    {
                        "type": "rate",
                        "name": "readmission_rate",
                        "numerator": "readmission_count",
                        "denominator": "episode_count"
                    },
                    {
                        "type": "avg",
                        "name": "avg_los",
                        "field": "los_days"
                    }
                ],
                "time_range": {
                    "start": "2025-01-01T00:00:00Z",
                    "end": "2025-01-31T23:59:59Z"
                },
                "limit": 1000
            }
        }


class CohortQueryResult(BaseModel):
    """Single row in cohort query results"""

    dimensions: Dict[str, Any] = Field(..., description="Grouping dimension values")
    metrics: Dict[str, float] = Field(..., description="Calculated metric values")
    sample_size: int = Field(..., description="Number of records in this group")


class CohortQueryResponse(BaseModel):
    """Response from cohort query execution"""

    query_id: str = Field(..., description="Unique query execution ID")
    tenant_id: UUID
    executed_at: datetime
    execution_time_ms: int
    total_results: int
    results: List[CohortQueryResult]
    query_dsl: Dict[str, Any] = Field(..., description="The executed query DSL")
    warnings: Optional[List[str]] = None


# ==================== Data Dictionary Schemas ====================

class FieldDefinition(BaseModel):
    """Definition of a queryable field"""

    field_name: str
    display_name: str
    data_type: str  # string, integer, float, boolean, datetime, code
    entity: str  # episode, patient, encounter, etc.
    description: Optional[str] = None
    is_filterable: bool = Field(default=True)
    is_groupable: bool = Field(default=True)
    valid_operators: List[str] = Field(default_factory=list)
    code_system: Optional[str] = Field(None, description="For coded fields (ICD-10, SNOMED)")


class CodeSystemDefinition(BaseModel):
    """Definition of a code system"""

    code_system: str  # ICD-10, SNOMED-CT, LOINC, etc.
    version: Optional[str] = None
    total_codes: int
    sample_codes: List[Dict[str, str]] = Field(..., description="[{code, display}, ...]")


class MetricCatalogEntry(BaseModel):
    """Pre-defined metric in catalog"""

    code: str
    name: str
    description: str
    category: str  # safety, effectiveness, patient_experience, etc.
    calculation_type: str  # rate, count, avg, etc.
    definition_dsl: Dict[str, Any]


class DataDictionaryResponse(BaseModel):
    """Complete data dictionary"""

    fields: List[FieldDefinition]
    code_systems: List[CodeSystemDefinition]
    metrics_catalog: List[MetricCatalogEntry]
    entities: List[str] = Field(..., description="Available entity types")
    generated_at: datetime


# ==================== Warehouse Sync Schemas ====================

class WarehouseSyncRequest(BaseModel):
    """Request to trigger warehouse sync"""

    tenant_id: Optional[UUID] = Field(None, description="Sync specific tenant, or all if None")
    sync_type: str = Field(default="incremental", description="full, incremental")
    start_time: Optional[datetime] = Field(None, description="Start of sync window (for incremental)")
    end_time: Optional[datetime] = Field(None, description="End of sync window")
    tables: Optional[List[str]] = Field(None, description="Specific tables to sync, or all if None")
    force: bool = Field(default=False, description="Force full sync even if incremental requested")

    @validator("sync_type")
    def validate_sync_type(cls, v):
        valid_types = ["full", "incremental"]
        if v.lower() not in valid_types:
            raise ValueError(f"sync_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "sync_type": "incremental",
                "start_time": "2025-01-15T00:00:00Z",
                "end_time": "2025-01-15T23:59:59Z",
                "tables": ["episodes", "outcomes", "proms"],
                "force": False
            }
        }


class WarehouseSyncResponse(BaseModel):
    """Response from warehouse sync trigger"""

    sync_job_id: str
    tenant_id: Optional[UUID] = None
    sync_type: str
    status: str  # queued, running, completed, failed
    triggered_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tables_synced: Optional[List[str]] = None
    records_synced: Optional[int] = None
    warehouse_location: Optional[str] = Field(None, description="Warehouse table/dataset location")
    errors: Optional[List[str]] = None
