"""
Data Export and Import Service

EPIC-004: Multi-Tenancy Implementation
US-004.5: Tenant Data Management
US-004.7: Tenant Migration Tools

Provides comprehensive data management:
- Full tenant data export
- Partial data export
- GDPR data portability
- Data import with validation
- Tenant migration between environments
"""

import asyncio
import gzip
import json
import logging
import os
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4
import hashlib

from sqlalchemy import text
from sqlalchemy.orm import Session

from .tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    JSON_LINES = "jsonl"
    CSV = "csv"
    FHIR_BUNDLE = "fhir_bundle"


class ExportStatus(str, Enum):
    """Export job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ImportStatus(str, Enum):
    """Import job status."""
    PENDING = "pending"
    VALIDATING = "validating"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ExportConfig:
    """Configuration for data export."""
    tenant_id: str
    export_type: str = "full"  # full, partial, gdpr
    format: ExportFormat = ExportFormat.JSON
    include_tables: Optional[List[str]] = None
    exclude_tables: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    compress: bool = True
    encrypt: bool = False
    include_audit_logs: bool = False
    include_attachments: bool = False


@dataclass
class ImportConfig:
    """Configuration for data import."""
    tenant_id: str
    source_file: str
    format: ExportFormat = ExportFormat.JSON
    mode: str = "merge"  # merge, replace, append
    validate_only: bool = False
    skip_errors: bool = False
    batch_size: int = 1000


@dataclass
class ExportResult:
    """Result of an export operation."""
    export_id: str
    status: ExportStatus
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    records_exported: int = 0
    tables_exported: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    checksum: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


@dataclass
class ImportResult:
    """Result of an import operation."""
    import_id: str
    status: ImportStatus
    records_imported: int = 0
    records_skipped: int = 0
    records_failed: int = 0
    tables_imported: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# Tables that can be exported for each tenant
EXPORTABLE_TABLES = [
    "patients",
    "patient_identifiers",
    "practitioners",
    "organizations",
    "locations",
    "users",
    "roles",
    "appointments",
    "encounters",
    "consents",
    "communications",
    "tickets",
    "journeys",
    "journey_stages",
    "journey_instances",
    "journey_stage_instances",
    "provider_schedules",
    "schedule_overrides",
]

# Tables with PHI that require special handling
PHI_TABLES = [
    "patients",
    "patient_identifiers",
    "encounters",
    "communications",
]


class DataExporter:
    """
    Handles data export for tenants.

    Supports multiple formats and partial exports.
    """

    def __init__(
        self,
        db_session_factory,
        storage_backend=None,  # S3, local, etc.
        encryption_key: Optional[str] = None,
    ):
        self.db_factory = db_session_factory
        self.storage = storage_backend
        self.encryption_key = encryption_key

    async def export(self, config: ExportConfig) -> ExportResult:
        """
        Export tenant data according to configuration.

        Args:
            config: Export configuration

        Returns:
            ExportResult with file path and statistics
        """
        export_id = str(uuid4())
        started_at = datetime.now(timezone.utc)

        result = ExportResult(
            export_id=export_id,
            status=ExportStatus.PROCESSING,
            started_at=started_at,
            expires_at=started_at + timedelta(days=7),
        )

        try:
            # Determine tables to export
            tables = config.include_tables or EXPORTABLE_TABLES
            if config.exclude_tables:
                tables = [t for t in tables if t not in config.exclude_tables]

            # Create temp file for export
            suffix = self._get_file_suffix(config.format, config.compress)
            temp_file = tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=suffix,
                delete=False,
            )

            try:
                # Export based on format
                if config.format == ExportFormat.JSON:
                    records = await self._export_json(
                        config.tenant_id, tables, config, temp_file
                    )
                elif config.format == ExportFormat.JSON_LINES:
                    records = await self._export_jsonl(
                        config.tenant_id, tables, config, temp_file
                    )
                elif config.format == ExportFormat.FHIR_BUNDLE:
                    records = await self._export_fhir(
                        config.tenant_id, tables, config, temp_file
                    )
                else:
                    raise ValueError(f"Unsupported format: {config.format}")

                temp_file.close()

                # Calculate checksum
                checksum = self._calculate_checksum(temp_file.name)

                # Get file size
                file_size = os.path.getsize(temp_file.name)

                # Move to permanent storage
                if self.storage:
                    permanent_path = await self._upload_to_storage(
                        temp_file.name, export_id, config
                    )
                else:
                    permanent_path = temp_file.name

                result.status = ExportStatus.COMPLETED
                result.file_path = permanent_path
                result.file_size = file_size
                result.records_exported = records
                result.tables_exported = tables
                result.checksum = checksum
                result.completed_at = datetime.now(timezone.utc)

            finally:
                if self.storage and os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

        except Exception as e:
            logger.error(f"Export failed: {e}")
            result.status = ExportStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.now(timezone.utc)

        # Save export record to database
        await self._save_export_record(config.tenant_id, result)

        return result

    async def _export_json(
        self,
        tenant_id: str,
        tables: List[str],
        config: ExportConfig,
        output_file,
    ) -> int:
        """Export data as JSON."""
        total_records = 0
        data = {
            "export_id": str(uuid4()),
            "tenant_id": tenant_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "format_version": "1.0",
            "tables": {},
        }

        db = self.db_factory()
        try:
            for table in tables:
                records = await self._fetch_table_data(
                    db, tenant_id, table, config.date_from, config.date_to
                )
                data["tables"][table] = records
                total_records += len(records)

        finally:
            db.close()

        # Write to file
        json_data = json.dumps(data, default=str, indent=2)

        if config.compress:
            output_file.write(gzip.compress(json_data.encode("utf-8")))
        else:
            output_file.write(json_data.encode("utf-8"))

        return total_records

    async def _export_jsonl(
        self,
        tenant_id: str,
        tables: List[str],
        config: ExportConfig,
        output_file,
    ) -> int:
        """Export data as JSON Lines (one record per line)."""
        total_records = 0

        db = self.db_factory()
        try:
            lines = []

            # Header line
            lines.append(json.dumps({
                "type": "header",
                "tenant_id": tenant_id,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "format_version": "1.0",
            }))

            for table in tables:
                records = await self._fetch_table_data(
                    db, tenant_id, table, config.date_from, config.date_to
                )

                for record in records:
                    lines.append(json.dumps({
                        "type": "record",
                        "table": table,
                        "data": record,
                    }, default=str))

                total_records += len(records)

        finally:
            db.close()

        content = "\n".join(lines)

        if config.compress:
            output_file.write(gzip.compress(content.encode("utf-8")))
        else:
            output_file.write(content.encode("utf-8"))

        return total_records

    async def _export_fhir(
        self,
        tenant_id: str,
        tables: List[str],
        config: ExportConfig,
        output_file,
    ) -> int:
        """Export data as FHIR Bundle."""
        bundle = {
            "resourceType": "Bundle",
            "id": str(uuid4()),
            "type": "collection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry": [],
        }

        total_records = 0

        db = self.db_factory()
        try:
            # Map tables to FHIR resources
            fhir_mappings = {
                "patients": "Patient",
                "practitioners": "Practitioner",
                "organizations": "Organization",
                "locations": "Location",
                "appointments": "Appointment",
                "encounters": "Encounter",
            }

            for table in tables:
                if table not in fhir_mappings:
                    continue

                records = await self._fetch_table_data(
                    db, tenant_id, table, config.date_from, config.date_to
                )

                for record in records:
                    # Use stored FHIR resource if available
                    fhir_resource = record.get("fhir_resource")
                    if fhir_resource:
                        bundle["entry"].append({
                            "resource": fhir_resource,
                        })
                    else:
                        # Convert to basic FHIR structure
                        bundle["entry"].append({
                            "resource": {
                                "resourceType": fhir_mappings[table],
                                "id": str(record.get("id")),
                                **{k: v for k, v in record.items() if k != "id"},
                            },
                        })

                total_records += len(records)

        finally:
            db.close()

        json_data = json.dumps(bundle, default=str, indent=2)

        if config.compress:
            output_file.write(gzip.compress(json_data.encode("utf-8")))
        else:
            output_file.write(json_data.encode("utf-8"))

        return total_records

    async def _fetch_table_data(
        self,
        db: Session,
        tenant_id: str,
        table: str,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
    ) -> List[Dict]:
        """Fetch data from a table with date filtering."""
        conditions = ["tenant_id = :tenant_id"]
        params = {"tenant_id": tenant_id}

        if date_from:
            conditions.append("created_at >= :date_from")
            params["date_from"] = date_from

        if date_to:
            conditions.append("created_at <= :date_to")
            params["date_to"] = date_to

        where_clause = " AND ".join(conditions)

        try:
            results = db.execute(
                text(f"SELECT * FROM {table} WHERE {where_clause}"),
                params
            ).fetchall()

            return [dict(r._mapping) for r in results]
        except Exception as e:
            logger.warning(f"Failed to export table {table}: {e}")
            return []

    def _get_file_suffix(self, format: ExportFormat, compress: bool) -> str:
        """Get file suffix based on format and compression."""
        suffixes = {
            ExportFormat.JSON: ".json",
            ExportFormat.JSON_LINES: ".jsonl",
            ExportFormat.CSV: ".csv",
            ExportFormat.FHIR_BUNDLE: ".fhir.json",
        }
        suffix = suffixes.get(format, ".json")
        if compress:
            suffix += ".gz"
        return suffix

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def _upload_to_storage(
        self,
        temp_path: str,
        export_id: str,
        config: ExportConfig,
    ) -> str:
        """Upload export file to permanent storage."""
        # TODO: Implement actual storage upload (S3, GCS, etc.)
        # For now, return the temp path
        return temp_path

    async def _save_export_record(self, tenant_id: str, result: ExportResult):
        """Save export record to database."""
        db = self.db_factory()
        try:
            db.execute(
                text("""
                    UPDATE tenant_data_exports
                    SET status = :status, file_path = :file_path, file_size_bytes = :file_size,
                        records_exported = :records, error_message = :error,
                        started_at = :started_at, completed_at = :completed_at
                    WHERE id = :id
                """),
                {
                    "id": result.export_id,
                    "status": result.status.value,
                    "file_path": result.file_path,
                    "file_size": result.file_size,
                    "records": result.records_exported,
                    "error": result.errors[0] if result.errors else None,
                    "started_at": result.started_at,
                    "completed_at": result.completed_at,
                }
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save export record: {e}")
            db.rollback()
        finally:
            db.close()


class DataImporter:
    """
    Handles data import for tenants.

    Supports validation, merge strategies, and rollback.
    """

    def __init__(self, db_session_factory, storage_backend=None):
        self.db_factory = db_session_factory
        self.storage = storage_backend

    async def import_data(self, config: ImportConfig) -> ImportResult:
        """
        Import data into tenant.

        Args:
            config: Import configuration

        Returns:
            ImportResult with statistics
        """
        import_id = str(uuid4())
        started_at = datetime.now(timezone.utc)

        result = ImportResult(
            import_id=import_id,
            status=ImportStatus.VALIDATING,
            started_at=started_at,
        )

        try:
            # Load and parse import file
            data = await self._load_import_file(config.source_file, config.format)

            # Validate data structure
            validation_errors = await self._validate_data(data, config)

            if validation_errors:
                if config.skip_errors:
                    result.errors.extend(validation_errors)
                else:
                    result.status = ImportStatus.FAILED
                    result.errors = validation_errors
                    return result

            if config.validate_only:
                result.status = ImportStatus.COMPLETED
                return result

            # Import data
            result.status = ImportStatus.IMPORTING
            records_imported, records_failed, tables = await self._import_records(
                config.tenant_id, data, config
            )

            result.records_imported = records_imported
            result.records_failed = records_failed
            result.tables_imported = tables
            result.status = ImportStatus.COMPLETED
            result.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Import failed: {e}")
            result.status = ImportStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.now(timezone.utc)

        return result

    async def _load_import_file(
        self,
        file_path: str,
        format: ExportFormat,
    ) -> Dict[str, Any]:
        """Load and parse import file."""
        # Check if compressed
        is_compressed = file_path.endswith(".gz")

        if is_compressed:
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                content = f.read()
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

        if format == ExportFormat.JSON:
            return json.loads(content)
        elif format == ExportFormat.JSON_LINES:
            lines = content.strip().split("\n")
            data = {"tables": {}}
            for line in lines:
                record = json.loads(line)
                if record.get("type") == "record":
                    table = record["table"]
                    if table not in data["tables"]:
                        data["tables"][table] = []
                    data["tables"][table].append(record["data"])
            return data
        else:
            raise ValueError(f"Unsupported import format: {format}")

    async def _validate_data(
        self,
        data: Dict[str, Any],
        config: ImportConfig,
    ) -> List[str]:
        """Validate import data structure."""
        errors = []

        if "tables" not in data:
            errors.append("Missing 'tables' key in import data")
            return errors

        for table, records in data["tables"].items():
            if table not in EXPORTABLE_TABLES:
                errors.append(f"Unknown table: {table}")
                continue

            if not isinstance(records, list):
                errors.append(f"Table {table} records must be a list")
                continue

            for i, record in enumerate(records):
                if not isinstance(record, dict):
                    errors.append(f"Table {table} record {i} must be a dict")
                    continue

                if "id" not in record:
                    errors.append(f"Table {table} record {i} missing 'id' field")

        return errors

    async def _import_records(
        self,
        tenant_id: str,
        data: Dict[str, Any],
        config: ImportConfig,
    ) -> Tuple[int, int, List[str]]:
        """Import records into database."""
        total_imported = 0
        total_failed = 0
        tables_imported = []

        db = self.db_factory()
        try:
            # Bypass RLS for import
            db.execute(text("SELECT set_bypass_rls(true)"))

            for table, records in data["tables"].items():
                try:
                    imported, failed = await self._import_table(
                        db, tenant_id, table, records, config
                    )
                    total_imported += imported
                    total_failed += failed
                    if imported > 0:
                        tables_imported.append(table)
                except Exception as e:
                    logger.error(f"Failed to import table {table}: {e}")
                    total_failed += len(records)
                    if not config.skip_errors:
                        raise

            db.execute(text("SELECT set_bypass_rls(false)"))
            db.commit()

        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

        return total_imported, total_failed, tables_imported

    async def _import_table(
        self,
        db: Session,
        tenant_id: str,
        table: str,
        records: List[Dict],
        config: ImportConfig,
    ) -> Tuple[int, int]:
        """Import records into a single table."""
        imported = 0
        failed = 0

        for record in records:
            try:
                # Override tenant_id with target tenant
                record["tenant_id"] = tenant_id

                if config.mode == "merge":
                    # Try update, then insert
                    result = db.execute(
                        text(f"SELECT id FROM {table} WHERE id = :id"),
                        {"id": record["id"]}
                    ).fetchone()

                    if result:
                        # Update existing
                        columns = [k for k in record.keys() if k != "id"]
                        set_clause = ", ".join(f"{col} = :{col}" for col in columns)
                        db.execute(
                            text(f"UPDATE {table} SET {set_clause} WHERE id = :id"),
                            record
                        )
                    else:
                        # Insert new
                        columns = list(record.keys())
                        values = ", ".join(f":{col}" for col in columns)
                        db.execute(
                            text(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values})"),
                            record
                        )

                elif config.mode == "append":
                    # Generate new ID and insert
                    record["id"] = str(uuid4())
                    columns = list(record.keys())
                    values = ", ".join(f":{col}" for col in columns)
                    db.execute(
                        text(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values})"),
                        record
                    )

                elif config.mode == "replace":
                    # Delete existing and insert
                    db.execute(
                        text(f"DELETE FROM {table} WHERE id = :id"),
                        {"id": record["id"]}
                    )
                    columns = list(record.keys())
                    values = ", ".join(f":{col}" for col in columns)
                    db.execute(
                        text(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values})"),
                        record
                    )

                imported += 1

            except Exception as e:
                logger.warning(f"Failed to import record in {table}: {e}")
                failed += 1
                if not config.skip_errors:
                    raise

        return imported, failed


class TenantMigrator:
    """
    Handles tenant migration between environments.

    Supports full tenant migration with data, configuration, and resources.
    """

    def __init__(
        self,
        source_db_factory,
        target_db_factory,
        source_storage=None,
        target_storage=None,
    ):
        self.source_db = source_db_factory
        self.target_db = target_db_factory
        self.source_storage = source_storage
        self.target_storage = target_storage
        self.exporter = DataExporter(source_db_factory)
        self.importer = DataImporter(target_db_factory)

    async def migrate_tenant(
        self,
        source_tenant_id: str,
        target_tenant_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Migrate a tenant from source to target environment.

        Args:
            source_tenant_id: Tenant ID in source environment
            target_tenant_id: Optional new tenant ID (generates new if not provided)
            dry_run: If True, validate only without making changes

        Returns:
            Migration result with statistics
        """
        target_tenant_id = target_tenant_id or str(uuid4())
        started_at = datetime.now(timezone.utc)

        result = {
            "migration_id": str(uuid4()),
            "source_tenant_id": source_tenant_id,
            "target_tenant_id": target_tenant_id,
            "dry_run": dry_run,
            "status": "in_progress",
            "started_at": started_at.isoformat(),
            "steps": [],
        }

        try:
            # Step 1: Export from source
            result["steps"].append({
                "step": "export",
                "status": "in_progress",
            })

            export_config = ExportConfig(
                tenant_id=source_tenant_id,
                export_type="full",
                format=ExportFormat.JSON,
                compress=True,
            )
            export_result = await self.exporter.export(export_config)

            if export_result.status != ExportStatus.COMPLETED:
                raise Exception(f"Export failed: {export_result.errors}")

            result["steps"][-1]["status"] = "completed"
            result["steps"][-1]["records_exported"] = export_result.records_exported

            if dry_run:
                result["status"] = "validated"
                result["message"] = "Dry run completed. Migration is valid."
                return result

            # Step 2: Import to target
            result["steps"].append({
                "step": "import",
                "status": "in_progress",
            })

            import_config = ImportConfig(
                tenant_id=target_tenant_id,
                source_file=export_result.file_path,
                format=ExportFormat.JSON,
                mode="replace",
            )
            import_result = await self.importer.import_data(import_config)

            if import_result.status != ImportStatus.COMPLETED:
                raise Exception(f"Import failed: {import_result.errors}")

            result["steps"][-1]["status"] = "completed"
            result["steps"][-1]["records_imported"] = import_result.records_imported

            # Step 3: Migrate storage (files, attachments)
            if self.source_storage and self.target_storage:
                result["steps"].append({
                    "step": "storage_migration",
                    "status": "in_progress",
                })

                files_migrated = await self._migrate_storage(
                    source_tenant_id, target_tenant_id
                )

                result["steps"][-1]["status"] = "completed"
                result["steps"][-1]["files_migrated"] = files_migrated

            result["status"] = "completed"
            result["completed_at"] = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["completed_at"] = datetime.now(timezone.utc).isoformat()

        return result

    async def _migrate_storage(
        self,
        source_tenant_id: str,
        target_tenant_id: str,
    ) -> int:
        """Migrate storage files from source to target."""
        # TODO: Implement storage migration (S3 to S3, etc.)
        return 0
