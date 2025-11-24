"""
FHIR Bundle Service
Handles FHIR Bundle operations including transaction and batch processing
"""
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from loguru import logger

from ..repository.fhir_repository import FHIRRepository
from ..validators.validator import FHIRValidator


class BundleService:
    """
    Service for FHIR Bundle operations
    Supports transaction, batch, history, and searchset bundles
    """

    def __init__(self, db: Session):
        """
        Initialize Bundle service

        Args:
            db: Database session
        """
        self.db = db
        self.repository = FHIRRepository(db)
        self.validator = FHIRValidator()

    def process_bundle(
        self,
        tenant_id: UUID,
        bundle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a FHIR Bundle

        Args:
            tenant_id: Tenant identifier
            bundle: FHIR Bundle resource

        Returns:
            Bundle with response entries

        Raises:
            ValueError: If bundle is invalid
        """
        # Validate bundle
        if bundle.get("resourceType") != "Bundle":
            raise ValueError("Resource must be a Bundle")

        bundle_type = bundle.get("type")
        if not bundle_type:
            raise ValueError("Bundle must have a type")

        # Route to appropriate handler
        if bundle_type == "transaction":
            return self._process_transaction_bundle(tenant_id, bundle)
        elif bundle_type == "batch":
            return self._process_batch_bundle(tenant_id, bundle)
        else:
            raise ValueError(f"Unsupported bundle type: {bundle_type}")

    def _process_transaction_bundle(
        self,
        tenant_id: UUID,
        bundle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a transaction bundle (all-or-nothing)

        Args:
            tenant_id: Tenant identifier
            bundle: Transaction bundle

        Returns:
            Bundle with response entries
        """
        entries = bundle.get("entry", [])
        response_entries = []

        try:
            # Process all entries in a transaction
            for entry in entries:
                request = entry.get("request", {})
                method = request.get("method")
                url = request.get("url", "")
                resource = entry.get("resource")

                # Process each request
                response = self._process_bundle_request(
                    tenant_id, method, url, resource
                )
                response_entries.append(response)

            # If we get here, all operations succeeded
            self.db.commit()

            # Build response bundle
            response_bundle = {
                "resourceType": "Bundle",
                "type": "transaction-response",
                "entry": response_entries
            }

            logger.info(f"Processed transaction bundle with {len(entries)} entries")
            return response_bundle

        except Exception as e:
            # Rollback all changes on any error
            self.db.rollback()
            logger.error(f"Transaction bundle failed: {e}")

            # Build error response
            return self._build_error_bundle(str(e), entries)

    def _process_batch_bundle(
        self,
        tenant_id: UUID,
        bundle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a batch bundle (independent operations)

        Args:
            tenant_id: Tenant identifier
            bundle: Batch bundle

        Returns:
            Bundle with response entries
        """
        entries = bundle.get("entry", [])
        response_entries = []

        # Process each entry independently
        for entry in entries:
            try:
                request = entry.get("request", {})
                method = request.get("method")
                url = request.get("url", "")
                resource = entry.get("resource")

                # Process request
                response = self._process_bundle_request(
                    tenant_id, method, url, resource
                )
                response_entries.append(response)

                # Commit each operation independently
                self.db.commit()

            except Exception as e:
                # Rollback this operation but continue with others
                self.db.rollback()
                logger.error(f"Batch entry failed: {e}")

                # Add error response for this entry
                response_entries.append({
                    "response": {
                        "status": "400 Bad Request",
                        "outcome": {
                            "resourceType": "OperationOutcome",
                            "issue": [{
                                "severity": "error",
                                "code": "processing",
                                "diagnostics": str(e)
                            }]
                        }
                    }
                })

        # Build response bundle
        response_bundle = {
            "resourceType": "Bundle",
            "type": "batch-response",
            "entry": response_entries
        }

        logger.info(f"Processed batch bundle with {len(entries)} entries")
        return response_bundle

    def _process_bundle_request(
        self,
        tenant_id: UUID,
        method: str,
        url: str,
        resource: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a single bundle request

        Args:
            tenant_id: Tenant identifier
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            resource: Resource data (for POST/PUT)

        Returns:
            Response entry
        """
        # Parse URL to extract resource type and ID
        url_parts = url.strip('/').split('/')
        resource_type = url_parts[0] if url_parts else None
        resource_id = url_parts[1] if len(url_parts) > 1 else None

        if method == "POST":
            # Create resource
            if not resource:
                raise ValueError(f"POST requires a resource: {url}")

            created = self.repository.create(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_data=resource
            )

            return {
                "response": {
                    "status": "201 Created",
                    "location": f"/{resource_type}/{created['id']}",
                    "etag": f"W/\"{created.get('meta', {}).get('versionId', '1')}\"",
                    "lastModified": created.get("meta", {}).get("lastUpdated")
                },
                "resource": created
            }

        elif method == "PUT":
            # Update resource
            if not resource or not resource_id:
                raise ValueError(f"PUT requires a resource and ID: {url}")

            updated = self.repository.update(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_data=resource
            )

            return {
                "response": {
                    "status": "200 OK",
                    "location": f"/{resource_type}/{resource_id}",
                    "etag": f"W/\"{updated.get('meta', {}).get('versionId', '1')}\"",
                    "lastModified": updated.get("meta", {}).get("lastUpdated")
                },
                "resource": updated
            }

        elif method == "GET":
            # Read resource
            if not resource_id:
                raise ValueError(f"GET requires a resource ID: {url}")

            found = self.repository.get_by_id(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id
            )

            if not found:
                raise ValueError(f"Resource not found: {url}")

            return {
                "response": {
                    "status": "200 OK",
                    "etag": f"W/\"{found.get('meta', {}).get('versionId', '1')}\"",
                    "lastModified": found.get("meta", {}).get("lastUpdated")
                },
                "resource": found
            }

        elif method == "DELETE":
            # Delete resource
            if not resource_id:
                raise ValueError(f"DELETE requires a resource ID: {url}")

            deleted = self.repository.delete(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id
            )

            if not deleted:
                raise ValueError(f"Resource not found: {url}")

            return {
                "response": {
                    "status": "204 No Content"
                }
            }

        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def _build_error_bundle(
        self,
        error_message: str,
        entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build an error response bundle

        Args:
            error_message: Error message
            entries: Original bundle entries

        Returns:
            Error bundle
        """
        return {
            "resourceType": "Bundle",
            "type": "transaction-response",
            "entry": [
                {
                    "response": {
                        "status": "400 Bad Request",
                        "outcome": {
                            "resourceType": "OperationOutcome",
                            "issue": [{
                                "severity": "error",
                                "code": "processing",
                                "diagnostics": error_message
                            }]
                        }
                    }
                }
                for _ in entries
            ]
        }

    def create_search_bundle(
        self,
        resource_type: str,
        resources: List[Dict[str, Any]],
        total: int,
        base_url: str,
        count: int,
        offset: int
    ) -> Dict[str, Any]:
        """
        Create a searchset Bundle from search results

        Args:
            resource_type: Type of resources
            resources: List of resources
            total: Total number of matching resources
            base_url: Base URL for links
            count: Number of results per page
            offset: Current offset

        Returns:
            Searchset Bundle
        """
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": total,
            "link": [
                {
                    "relation": "self",
                    "url": f"{base_url}?_count={count}&_offset={offset}"
                }
            ],
            "entry": []
        }

        # Add pagination links
        if offset > 0:
            bundle["link"].append({
                "relation": "previous",
                "url": f"{base_url}?_count={count}&_offset={max(0, offset - count)}"
            })

        if offset + count < total:
            bundle["link"].append({
                "relation": "next",
                "url": f"{base_url}?_count={count}&_offset={offset + count}"
            })

        # Add resources
        for resource in resources:
            bundle["entry"].append({
                "fullUrl": f"/{resource_type}/{resource.get('id')}",
                "resource": resource,
                "search": {
                    "mode": "match"
                }
            })

        return bundle

    def create_history_bundle(
        self,
        resource_type: str,
        resource_id: str,
        versions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a history Bundle from resource versions

        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            versions: List of versions

        Returns:
            History Bundle
        """
        bundle = {
            "resourceType": "Bundle",
            "type": "history",
            "total": len(versions),
            "entry": []
        }

        for version in versions:
            version_id = version.get("meta", {}).get("versionId", "1")
            bundle["entry"].append({
                "fullUrl": f"/{resource_type}/{resource_id}/_history/{version_id}",
                "resource": version,
                "request": {
                    "method": "GET",
                    "url": f"{resource_type}/{resource_id}"
                },
                "response": {
                    "status": "200 OK",
                    "lastModified": version.get("meta", {}).get("lastUpdated")
                }
            })

        return bundle

    def validate_bundle(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a FHIR Bundle

        Args:
            bundle: Bundle to validate

        Returns:
            OperationOutcome with validation results
        """
        validation_result = self.validator.validate_bundle(bundle)
        return validation_result.to_operation_outcome()
