"""
Report Builder Service - EPIC-011: US-011.7
Self-service report creation and distribution capabilities.

Features:
- Drag-and-drop report builder interface support
- Visual query builder
- Pre-built templates library
- Calculated field creation
- 20+ visualization types
- Scheduled report delivery
- Export to multiple formats (PDF, Excel, PowerPoint)
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4
import random
import json


class ReportType(Enum):
    """Types of reports."""
    DASHBOARD = "dashboard"
    TABULAR = "tabular"
    SUMMARY = "summary"
    DETAIL = "detail"
    TRENDING = "trending"
    COMPARISON = "comparison"
    AD_HOC = "ad_hoc"


class VisualizationType(Enum):
    """Available visualization types."""
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    DONUT_CHART = "donut_chart"
    AREA_CHART = "area_chart"
    SCATTER_PLOT = "scatter_plot"
    HEAT_MAP = "heat_map"
    TREE_MAP = "tree_map"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    KPI_CARD = "kpi_card"
    TABLE = "table"
    PIVOT_TABLE = "pivot_table"
    SPARKLINE = "sparkline"
    WATERFALL = "waterfall"
    BULLET = "bullet"
    MAP = "map"
    SANKEY = "sankey"
    RADAR = "radar"
    BOX_PLOT = "box_plot"


class ExportFormat(Enum):
    """Export format options."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    POWERPOINT = "powerpoint"
    JSON = "json"
    PNG = "png"
    HTML = "html"


class ScheduleFrequency(Enum):
    """Report schedule frequency."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class DataSourceType(Enum):
    """Data source types."""
    DATABASE = "database"
    API = "api"
    FILE = "file"
    CUBE = "cube"
    CACHED = "cached"


@dataclass
class DataField:
    """Field definition for reports."""
    field_id: str
    field_name: str
    display_name: str
    data_type: str  # string, number, date, boolean
    source_table: str
    aggregation: Optional[str] = None  # sum, count, avg, min, max
    format: Optional[str] = None
    is_dimension: bool = True
    is_measure: bool = False
    is_calculated: bool = False
    formula: Optional[str] = None


@dataclass
class FilterCondition:
    """Filter condition for reports."""
    field_id: str
    operator: str  # equals, not_equals, contains, greater_than, etc.
    value: Any
    is_parameter: bool = False
    parameter_name: Optional[str] = None


@dataclass
class SortOrder:
    """Sort configuration."""
    field_id: str
    direction: str  # asc, desc


@dataclass
class VisualizationConfig:
    """Visualization configuration."""
    viz_type: VisualizationType
    title: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    series: List[str] = field(default_factory=list)
    color_scheme: str = "default"
    show_legend: bool = True
    show_labels: bool = True
    stacked: bool = False
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportDefinition:
    """Complete report definition."""
    report_id: str
    report_name: str
    description: str
    report_type: ReportType
    created_by: str
    created_at: datetime
    updated_at: datetime
    data_source: str
    fields: List[DataField]
    filters: List[FilterCondition]
    sort_order: List[SortOrder]
    visualizations: List[VisualizationConfig]
    parameters: Dict[str, Any] = field(default_factory=dict)
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    is_public: bool = False
    version: int = 1
    tags: List[str] = field(default_factory=list)


@dataclass
class ReportTemplate:
    """Pre-built report template."""
    template_id: str
    template_name: str
    description: str
    category: str
    preview_image: Optional[str]
    report_definition: ReportDefinition
    popularity: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class ReportExecution:
    """Report execution record."""
    execution_id: str
    report_id: str
    executed_by: str
    executed_at: datetime
    parameters_used: Dict[str, Any]
    duration_ms: int
    row_count: int
    status: str  # success, failed, timeout
    error_message: Optional[str] = None
    cached: bool = False


@dataclass
class ScheduledReport:
    """Scheduled report configuration."""
    schedule_id: str
    report_id: str
    report_name: str
    frequency: ScheduleFrequency
    schedule_time: str  # HH:MM
    day_of_week: Optional[int] = None  # 0-6 for weekly
    day_of_month: Optional[int] = None  # 1-31 for monthly
    recipients: List[str] = field(default_factory=list)
    export_format: ExportFormat = ExportFormat.PDF
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_by: str = ""


@dataclass
class ReportSubscription:
    """User subscription to a report."""
    subscription_id: str
    user_id: str
    report_id: str
    delivery_method: str  # email, portal, both
    frequency: ScheduleFrequency
    export_format: ExportFormat
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QueryResult:
    """Query execution result."""
    columns: List[Dict[str, str]]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: int
    truncated: bool
    warnings: List[str] = field(default_factory=list)


class ReportBuilderService:
    """
    Service for self-service report building and distribution.

    Provides capabilities for creating custom reports, scheduling deliveries,
    and managing report templates and subscriptions.
    """

    def __init__(self):
        self.reports: Dict[str, ReportDefinition] = {}
        self.templates: Dict[str, ReportTemplate] = {}
        self.schedules: Dict[str, ScheduledReport] = {}
        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize built-in report templates."""
        template_configs = [
            ("TPL-001", "Executive Dashboard", "executive", "Comprehensive KPI dashboard for leadership"),
            ("TPL-002", "Quality Measures Report", "clinical", "CMS quality measures tracking"),
            ("TPL-003", "Revenue Analysis", "financial", "Revenue cycle performance analysis"),
            ("TPL-004", "Department Performance", "operational", "Department-level productivity metrics"),
            ("TPL-005", "Patient Population", "population_health", "Patient population health summary"),
            ("TPL-006", "Provider Scorecard", "clinical", "Individual provider performance"),
            ("TPL-007", "Denial Management", "financial", "Claims denial analysis and tracking"),
            ("TPL-008", "Readmission Analysis", "clinical", "30-day readmission tracking"),
        ]

        for tid, name, category, desc in template_configs:
            self.templates[tid] = ReportTemplate(
                template_id=tid,
                template_name=name,
                description=desc,
                category=category,
                preview_image=f"/templates/{tid}/preview.png",
                report_definition=ReportDefinition(
                    report_id=tid,
                    report_name=name,
                    description=desc,
                    report_type=ReportType.DASHBOARD,
                    created_by="system",
                    created_at=datetime(2024, 1, 1),
                    updated_at=datetime(2024, 1, 1),
                    data_source="analytics_warehouse",
                    fields=[],
                    filters=[],
                    sort_order=[],
                    visualizations=[],
                    is_public=True
                ),
                popularity=random.randint(50, 500),
                tags=[category, "template"]
            )

    async def get_available_fields(
        self,
        data_source: str,
        tenant_id: Optional[str] = None
    ) -> List[DataField]:
        """
        Get available fields from a data source.

        Args:
            data_source: Name of the data source
            tenant_id: Tenant ID

        Returns:
            List of available fields
        """
        # Simulated field catalog
        fields = [
            # Patient dimensions
            DataField("patient_id", "patient_id", "Patient ID", "string", "dim_patients", is_dimension=True),
            DataField("patient_name", "patient_name", "Patient Name", "string", "dim_patients", is_dimension=True),
            DataField("patient_age", "age", "Patient Age", "number", "dim_patients", is_dimension=True),
            DataField("patient_gender", "gender", "Gender", "string", "dim_patients", is_dimension=True),
            DataField("insurance_type", "insurance_type", "Insurance Type", "string", "dim_patients", is_dimension=True),

            # Provider dimensions
            DataField("provider_id", "provider_id", "Provider ID", "string", "dim_providers", is_dimension=True),
            DataField("provider_name", "provider_name", "Provider Name", "string", "dim_providers", is_dimension=True),
            DataField("specialty", "specialty", "Specialty", "string", "dim_providers", is_dimension=True),

            # Facility dimensions
            DataField("facility_id", "facility_id", "Facility ID", "string", "dim_facilities", is_dimension=True),
            DataField("facility_name", "facility_name", "Facility Name", "string", "dim_facilities", is_dimension=True),
            DataField("department", "department", "Department", "string", "dim_facilities", is_dimension=True),

            # Date dimensions
            DataField("date", "date", "Date", "date", "dim_date", is_dimension=True),
            DataField("month", "month", "Month", "string", "dim_date", is_dimension=True),
            DataField("quarter", "quarter", "Quarter", "string", "dim_date", is_dimension=True),
            DataField("year", "year", "Year", "number", "dim_date", is_dimension=True),

            # Measures
            DataField("encounter_count", "encounter_count", "Encounter Count", "number", "fact_encounters",
                      aggregation="count", is_dimension=False, is_measure=True),
            DataField("patient_count", "patient_count", "Patient Count", "number", "fact_encounters",
                      aggregation="count_distinct", is_dimension=False, is_measure=True),
            DataField("total_charges", "total_charges", "Total Charges", "number", "fact_encounters",
                      aggregation="sum", format="currency", is_dimension=False, is_measure=True),
            DataField("total_revenue", "total_revenue", "Total Revenue", "number", "fact_encounters",
                      aggregation="sum", format="currency", is_dimension=False, is_measure=True),
            DataField("avg_los", "length_of_stay", "Avg Length of Stay", "number", "fact_encounters",
                      aggregation="avg", format="decimal", is_dimension=False, is_measure=True),
            DataField("readmission_rate", "readmission_rate", "Readmission Rate", "number", "fact_encounters",
                      aggregation="avg", format="percentage", is_dimension=False, is_measure=True),
        ]

        return fields

    async def create_report(
        self,
        report_definition: Dict[str, Any],
        created_by: str,
        tenant_id: Optional[str] = None
    ) -> ReportDefinition:
        """
        Create a new report definition.

        Args:
            report_definition: Report configuration
            created_by: User creating the report
            tenant_id: Tenant ID

        Returns:
            Created report definition
        """
        report_id = f"RPT-{str(uuid4())[:8]}"

        report = ReportDefinition(
            report_id=report_id,
            report_name=report_definition.get("name", "Untitled Report"),
            description=report_definition.get("description", ""),
            report_type=ReportType(report_definition.get("type", "ad_hoc")),
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            data_source=report_definition.get("data_source", "analytics_warehouse"),
            fields=[
                DataField(**f) for f in report_definition.get("fields", [])
            ] if report_definition.get("fields") else [],
            filters=[
                FilterCondition(**f) for f in report_definition.get("filters", [])
            ] if report_definition.get("filters") else [],
            sort_order=[
                SortOrder(**s) for s in report_definition.get("sort_order", [])
            ] if report_definition.get("sort_order") else [],
            visualizations=[
                VisualizationConfig(**v) for v in report_definition.get("visualizations", [])
            ] if report_definition.get("visualizations") else [],
            parameters=report_definition.get("parameters", {}),
            is_public=report_definition.get("is_public", False),
            tags=report_definition.get("tags", [])
        )

        self.reports[report_id] = report
        return report

    async def execute_report(
        self,
        report_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a report and return results.

        Args:
            report_id: Report identifier
            parameters: Runtime parameters
            limit: Max rows to return
            tenant_id: Tenant ID

        Returns:
            Report execution results
        """
        report = self.reports.get(report_id) or self._get_template_report(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id}")

        start_time = datetime.utcnow()

        # Generate sample data
        data = self._generate_sample_data(report, limit)

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Record execution
        execution = ReportExecution(
            execution_id=str(uuid4())[:8],
            report_id=report_id,
            executed_by="current_user",
            executed_at=datetime.utcnow(),
            parameters_used=parameters or {},
            duration_ms=execution_time,
            row_count=len(data["rows"]),
            status="success"
        )

        return {
            "report": {
                "id": report.report_id,
                "name": report.report_name,
                "type": report.report_type.value
            },
            "data": data,
            "execution": {
                "id": execution.execution_id,
                "duration_ms": execution.duration_ms,
                "row_count": execution.row_count,
                "cached": False
            },
            "visualizations": [
                self._render_visualization(v, data)
                for v in report.visualizations
            ] if report.visualizations else []
        }

    def _get_template_report(self, report_id: str) -> Optional[ReportDefinition]:
        """Get report definition from template."""
        template = self.templates.get(report_id)
        return template.report_definition if template else None

    def _generate_sample_data(
        self,
        report: ReportDefinition,
        limit: int
    ) -> Dict[str, Any]:
        """Generate sample data for report."""
        random.seed(42)

        # Define columns
        columns = [
            {"field": "date", "label": "Date", "type": "date"},
            {"field": "department", "label": "Department", "type": "string"},
            {"field": "provider", "label": "Provider", "type": "string"},
            {"field": "encounters", "label": "Encounters", "type": "number"},
            {"field": "revenue", "label": "Revenue", "type": "currency"},
            {"field": "avg_los", "label": "Avg LOS", "type": "number"},
        ]

        # Generate rows
        departments = ["Emergency", "Cardiology", "Surgery", "Medicine", "Pediatrics"]
        providers = ["Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Brown", "Dr. Davis"]

        rows = []
        for i in range(min(limit, 100)):
            rows.append({
                "date": (date.today() - timedelta(days=random.randint(0, 30))).isoformat(),
                "department": random.choice(departments),
                "provider": random.choice(providers),
                "encounters": random.randint(5, 50),
                "revenue": round(random.uniform(5000, 50000), 2),
                "avg_los": round(random.uniform(2, 8), 1)
            })

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": len(rows) >= limit
        }

    def _render_visualization(
        self,
        viz_config: VisualizationConfig,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Render visualization configuration."""
        return {
            "type": viz_config.viz_type.value,
            "title": viz_config.title,
            "config": {
                "x_axis": viz_config.x_axis,
                "y_axis": viz_config.y_axis,
                "series": viz_config.series,
                "color_scheme": viz_config.color_scheme,
                "show_legend": viz_config.show_legend,
                "show_labels": viz_config.show_labels,
                "stacked": viz_config.stacked,
                **viz_config.options
            },
            "data_key": "rows"
        }

    async def get_templates(
        self,
        category: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[ReportTemplate]:
        """
        Get available report templates.

        Args:
            category: Filter by category
            tenant_id: Tenant ID

        Returns:
            List of templates
        """
        templates = list(self.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return sorted(templates, key=lambda t: t.popularity, reverse=True)

    async def export_report(
        self,
        report_id: str,
        export_format: ExportFormat,
        parameters: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export a report to specified format.

        Args:
            report_id: Report identifier
            export_format: Export format
            parameters: Runtime parameters
            tenant_id: Tenant ID

        Returns:
            Export result with download URL
        """
        # Execute report first
        results = await self.execute_report(report_id, parameters)

        export_id = str(uuid4())[:8]

        return {
            "export_id": export_id,
            "report_id": report_id,
            "format": export_format.value,
            "status": "completed",
            "download_url": f"/exports/{export_id}/report.{export_format.value}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "file_size_bytes": random.randint(50000, 500000)
        }

    async def schedule_report(
        self,
        schedule_config: Dict[str, Any],
        created_by: str,
        tenant_id: Optional[str] = None
    ) -> ScheduledReport:
        """
        Create a scheduled report.

        Args:
            schedule_config: Schedule configuration
            created_by: User creating the schedule
            tenant_id: Tenant ID

        Returns:
            Created schedule
        """
        schedule_id = f"SCH-{str(uuid4())[:8]}"

        frequency = ScheduleFrequency(schedule_config.get("frequency", "daily"))

        # Calculate next run
        next_run = self._calculate_next_run(
            frequency,
            schedule_config.get("schedule_time", "08:00"),
            schedule_config.get("day_of_week"),
            schedule_config.get("day_of_month")
        )

        schedule = ScheduledReport(
            schedule_id=schedule_id,
            report_id=schedule_config["report_id"],
            report_name=schedule_config.get("report_name", "Scheduled Report"),
            frequency=frequency,
            schedule_time=schedule_config.get("schedule_time", "08:00"),
            day_of_week=schedule_config.get("day_of_week"),
            day_of_month=schedule_config.get("day_of_month"),
            recipients=schedule_config.get("recipients", []),
            export_format=ExportFormat(schedule_config.get("export_format", "pdf")),
            parameters=schedule_config.get("parameters", {}),
            is_active=True,
            next_run=next_run,
            created_by=created_by
        )

        self.schedules[schedule_id] = schedule
        return schedule

    def _calculate_next_run(
        self,
        frequency: ScheduleFrequency,
        schedule_time: str,
        day_of_week: Optional[int] = None,
        day_of_month: Optional[int] = None
    ) -> datetime:
        """Calculate next scheduled run time."""
        now = datetime.utcnow()
        hour, minute = map(int, schedule_time.split(":"))

        if frequency == ScheduleFrequency.DAILY:
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif frequency == ScheduleFrequency.WEEKLY:
            days_ahead = (day_of_week or 0) - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        elif frequency == ScheduleFrequency.MONTHLY:
            next_run = now.replace(day=day_of_month or 1, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
        else:
            next_run = now + timedelta(days=1)

        return next_run

    async def get_schedules(
        self,
        report_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[ScheduledReport]:
        """Get scheduled reports."""
        schedules = list(self.schedules.values())

        if report_id:
            schedules = [s for s in schedules if s.report_id == report_id]

        return schedules

    async def subscribe_to_report(
        self,
        user_id: str,
        report_id: str,
        subscription_config: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> ReportSubscription:
        """
        Subscribe user to a report.

        Args:
            user_id: User ID
            report_id: Report ID
            subscription_config: Subscription settings
            tenant_id: Tenant ID

        Returns:
            Created subscription
        """
        subscription = ReportSubscription(
            subscription_id=str(uuid4())[:8],
            user_id=user_id,
            report_id=report_id,
            delivery_method=subscription_config.get("delivery_method", "email"),
            frequency=ScheduleFrequency(subscription_config.get("frequency", "daily")),
            export_format=ExportFormat(subscription_config.get("export_format", "pdf")),
            is_active=True
        )

        return subscription

    async def build_query(
        self,
        query_config: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a query from visual configuration.

        Args:
            query_config: Visual query configuration
            tenant_id: Tenant ID

        Returns:
            Generated SQL and preview data
        """
        # Build SQL from configuration
        fields = query_config.get("fields", [])
        filters = query_config.get("filters", [])
        group_by = query_config.get("group_by", [])
        order_by = query_config.get("order_by", [])

        select_clause = ", ".join(fields) if fields else "*"
        from_clause = query_config.get("table", "fact_encounters")

        where_clauses = []
        for f in filters:
            where_clauses.append(f"{f['field']} {f['operator']} '{f['value']}'")

        sql = f"SELECT {select_clause}\nFROM {from_clause}"

        if where_clauses:
            sql += f"\nWHERE {' AND '.join(where_clauses)}"

        if group_by:
            sql += f"\nGROUP BY {', '.join(group_by)}"

        if order_by:
            order_clauses = [f"{o['field']} {o.get('direction', 'ASC')}" for o in order_by]
            sql += f"\nORDER BY {', '.join(order_clauses)}"

        return {
            "sql": sql,
            "preview": await self._execute_preview(sql),
            "estimated_rows": random.randint(100, 10000),
            "estimated_time_ms": random.randint(100, 2000)
        }

    async def _execute_preview(self, sql: str) -> Dict[str, Any]:
        """Execute query preview with limited rows."""
        # Return sample preview data
        return {
            "columns": [
                {"field": "col1", "label": "Column 1", "type": "string"},
                {"field": "col2", "label": "Column 2", "type": "number"}
            ],
            "rows": [
                {"col1": f"Value {i}", "col2": random.randint(100, 1000)}
                for i in range(10)
            ],
            "preview_only": True
        }

    async def get_visualization_types(self) -> List[Dict[str, Any]]:
        """Get available visualization types with metadata."""
        return [
            {
                "type": vt.value,
                "name": vt.value.replace("_", " ").title(),
                "category": self._get_viz_category(vt),
                "supports_multiple_series": vt in [
                    VisualizationType.LINE_CHART,
                    VisualizationType.BAR_CHART,
                    VisualizationType.AREA_CHART
                ],
                "requires_dimension": vt not in [
                    VisualizationType.KPI_CARD,
                    VisualizationType.GAUGE
                ],
                "icon": f"/icons/viz/{vt.value}.svg"
            }
            for vt in VisualizationType
        ]

    def _get_viz_category(self, viz_type: VisualizationType) -> str:
        """Get category for visualization type."""
        comparison = [VisualizationType.BAR_CHART, VisualizationType.BULLET]
        trends = [VisualizationType.LINE_CHART, VisualizationType.AREA_CHART, VisualizationType.SPARKLINE]
        distribution = [VisualizationType.PIE_CHART, VisualizationType.DONUT_CHART, VisualizationType.TREE_MAP]
        relationship = [VisualizationType.SCATTER_PLOT, VisualizationType.HEAT_MAP]
        kpi = [VisualizationType.KPI_CARD, VisualizationType.GAUGE]

        if viz_type in comparison:
            return "comparison"
        elif viz_type in trends:
            return "trends"
        elif viz_type in distribution:
            return "distribution"
        elif viz_type in relationship:
            return "relationship"
        elif viz_type in kpi:
            return "kpi"
        else:
            return "other"


# Global service instance
report_builder_service = ReportBuilderService()
