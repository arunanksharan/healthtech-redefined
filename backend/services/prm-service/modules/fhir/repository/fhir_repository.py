"""
FHIR Repository
Data access layer for FHIR resources with versioning support
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.dialects.postgresql import insert
import json

# Import database models
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))
from shared.database.fhir_models import FHIRResource as FHIRResourceDB, FHIRResourceHistory
from loguru import logger


class FHIRRepository:
    """Repository for FHIR resource operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_data: Dict[str, Any],
        resource_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new FHIR resource
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            resource_data: Complete FHIR resource as dict
            resource_id: Optional resource ID (auto-generated if not provided)
            
        Returns:
            Created resource with metadata
        """
        try:
            # Generate resource ID if not provided
            if not resource_id:
                resource_id = str(uuid4())

            # Ensure resource has correct ID and metadata
            resource_data["id"] = resource_id
            resource_data["resourceType"] = resource_type

            # Add or update meta
            if "meta" not in resource_data:
                resource_data["meta"] = {}
            
            resource_data["meta"]["versionId"] = "1"
            resource_data["meta"]["lastUpdated"] = datetime.utcnow().isoformat() + "Z"

            # Extract search tokens (basic implementation)
            search_tokens = self._extract_search_tokens(resource_type, resource_data)

            # Create database record
            db_resource = FHIRResourceDB(
                id=uuid4(),
                tenant_id=tenant_id,
                resource_type=resource_type,
                fhir_id=resource_id,
                version_id=1,
                last_updated=datetime.utcnow(),
                resource_data=resource_data,
                search_tokens=search_tokens,
                deleted=False
            )

            # Create history record
            history_record = FHIRResourceHistory(
                id=uuid4(),
                resource_id=db_resource.id,
                tenant_id=tenant_id,
                resource_type=resource_type,
                fhir_id=resource_id,
                version_id=1,
                resource_data=resource_data,
                operation="create",
                changed_by="fhir_api",
                changed_at=datetime.utcnow()
            )

            self.db.add(db_resource)
            self.db.add(history_record)
            self.db.commit()
            self.db.refresh(db_resource)

            logger.info(f"Created FHIR resource: {resource_type}/{resource_id} (v1)")
            
            return resource_data

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating FHIR resource: {e}")
            raise

    def get_by_id(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get FHIR resource by ID

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            resource_id: Resource ID
            version: Specific version (optional, returns current if not specified)

        Returns:
            FHIR resource or None if not found
        """
        try:
            query = self.db.query(FHIRResourceDB).filter(
                and_(
                    FHIRResourceDB.tenant_id == tenant_id,
                    FHIRResourceDB.resource_type == resource_type,
                    FHIRResourceDB.fhir_id == resource_id,
                    FHIRResourceDB.deleted == False
                )
            )

            if version:
                query = query.filter(FHIRResourceDB.version_id == version)

            db_resource = query.first()

            if not db_resource:
                return None

            return db_resource.resource_data

        except Exception as e:
            logger.error(f"Error retrieving FHIR resource: {e}")
            raise

    def update(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        resource_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update FHIR resource (creates new version)

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            resource_id: Resource ID
            resource_data: Updated FHIR resource

        Returns:
            Updated resource with new version
        """
        try:
            # Get current resource
            current = self.db.query(FHIRResourceDB).filter(
                and_(
                    FHIRResourceDB.tenant_id == tenant_id,
                    FHIRResourceDB.resource_type == resource_type,
                    FHIRResourceDB.fhir_id == resource_id,
                    FHIRResourceDB.deleted == False
                )
            ).first()

            if not current:
                raise ValueError(f"Resource not found: {resource_type}/{resource_id}")

            # Calculate new version
            new_version = current.version_id + 1

            # Update resource metadata
            resource_data["id"] = resource_id
            resource_data["resourceType"] = resource_type

            if "meta" not in resource_data:
                resource_data["meta"] = {}

            resource_data["meta"]["versionId"] = str(new_version)
            resource_data["meta"]["lastUpdated"] = datetime.utcnow().isoformat() + "Z"

            # Extract search tokens
            search_tokens = self._extract_search_tokens(resource_type, resource_data)

            # Update current resource
            current.version_id = new_version
            current.last_updated = datetime.utcnow()
            current.resource_data = resource_data
            current.search_tokens = search_tokens

            # Create history record
            history_record = FHIRResourceHistory(
                id=uuid4(),
                resource_id=current.id,
                tenant_id=tenant_id,
                resource_type=resource_type,
                fhir_id=resource_id,
                version_id=new_version,
                resource_data=resource_data,
                operation="update",
                changed_by="fhir_api",
                changed_at=datetime.utcnow()
            )

            self.db.add(history_record)
            self.db.commit()
            self.db.refresh(current)

            logger.info(f"Updated FHIR resource: {resource_type}/{resource_id} (v{new_version})")

            return resource_data

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating FHIR resource: {e}")
            raise

    def delete(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str
    ) -> bool:
        """
        Delete FHIR resource (soft delete)

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            resource_id: Resource ID

        Returns:
            True if deleted successfully
        """
        try:
            current = self.db.query(FHIRResourceDB).filter(
                and_(
                    FHIRResourceDB.tenant_id == tenant_id,
                    FHIRResourceDB.resource_type == resource_type,
                    FHIRResourceDB.fhir_id == resource_id,
                    FHIRResourceDB.deleted == False
                )
            ).first()

            if not current:
                return False

            # Increment version for delete
            new_version = current.version_id + 1

            # Soft delete - mark as deleted
            current.deleted = True
            current.version_id = new_version
            current.last_updated = datetime.utcnow()

            # Update metadata in resource_data
            resource_data = current.resource_data.copy()
            if "meta" not in resource_data:
                resource_data["meta"] = {}
            resource_data["meta"]["versionId"] = str(new_version)
            resource_data["meta"]["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
            current.resource_data = resource_data

            # Create history record for delete
            history_record = FHIRResourceHistory(
                id=uuid4(),
                resource_id=current.id,
                tenant_id=tenant_id,
                resource_type=resource_type,
                fhir_id=resource_id,
                version_id=new_version,
                resource_data=resource_data,
                operation="delete",
                changed_by="fhir_api",
                changed_at=datetime.utcnow()
            )

            self.db.add(history_record)
            self.db.commit()

            logger.info(f"Deleted FHIR resource: {resource_type}/{resource_id}")

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting FHIR resource: {e}")
            raise

    def search(
        self,
        tenant_id: UUID,
        resource_type: str,
        search_params: Dict[str, Any],
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search FHIR resources

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            search_params: Search parameters
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            FHIR Bundle with search results
        """
        try:
            query = self.db.query(FHIRResourceDB).filter(
                and_(
                    FHIRResourceDB.tenant_id == tenant_id,
                    FHIRResourceDB.resource_type == resource_type,
                    FHIRResourceDB.deleted == False
                )
            )

            # Apply search parameters
            # This is a simplified implementation - full FHIR search is more complex
            for param, value in search_params.items():
                if param == "_id":
                    query = query.filter(FHIRResourceDB.fhir_id == value)
                elif param == "identifier":
                    # Search in search_tokens JSONB field
                    query = query.filter(
                        FHIRResourceDB.search_tokens['identifier'].astext.contains(value)
                    )
                elif param == "name":
                    # Search in search_tokens JSONB field
                    query = query.filter(
                        FHIRResourceDB.search_tokens['name'].astext.contains(value)
                    )
                # Add more search parameters as needed

            # Get total count
            total = query.count()

            # Apply pagination
            results = query.order_by(desc(FHIRResourceDB.last_updated)).offset(offset).limit(limit).all()

            # Build FHIR Bundle
            bundle = {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": total,
                "link": [
                    {
                        "relation": "self",
                        "url": f"/fhir/{resource_type}?_count={limit}&_offset={offset}"
                    }
                ],
                "entry": []
            }

            for result in results:
                bundle["entry"].append({
                    "fullUrl": f"/fhir/{resource_type}/{result.fhir_id}",
                    "resource": result.resource_data,
                    "search": {"mode": "match"}
                })

            return bundle

        except Exception as e:
            logger.error(f"Error searching FHIR resources: {e}")
            raise

    def get_history(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get version history for a resource

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of FHIR resource
            resource_id: Resource ID

        Returns:
            List of all versions
        """
        try:
            versions = self.db.query(FHIRResourceHistory).filter(
                and_(
                    FHIRResourceHistory.tenant_id == tenant_id,
                    FHIRResourceHistory.resource_type == resource_type,
                    FHIRResourceHistory.fhir_id == resource_id
                )
            ).order_by(desc(FHIRResourceHistory.version_id)).all()

            return [v.resource_data for v in versions]

        except Exception as e:
            logger.error(f"Error retrieving resource history: {e}")
            raise

    def _extract_search_tokens(self, resource_type: str, resource_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Extract search tokens from resource for indexing
        
        Args:
            resource_type: Type of FHIR resource
            resource_data: FHIR resource data
            
        Returns:
            Dictionary of search tokens
        """
        tokens = {}
        
        try:
            # Extract common fields
            if "id" in resource_data:
                tokens["_id"] = [resource_data["id"]]
            
            # Resource-specific extraction
            if resource_type == "Patient":
                if "identifier" in resource_data:
                    tokens["identifier"] = [id["value"] for id in resource_data["identifier"] if "value" in id]
                if "name" in resource_data:
                    names = []
                    for name in resource_data["name"]:
                        if "family" in name:
                            names.append(name["family"])
                        if "given" in name:
                            names.extend(name["given"])
                    tokens["name"] = names
                if "birthDate" in resource_data:
                    tokens["birthdate"] = [resource_data["birthDate"]]
                    
            elif resource_type == "Observation":
                if "code" in resource_data:
                    codes = []
                    if "coding" in resource_data["code"]:
                        codes = [c["code"] for c in resource_data["code"]["coding"] if "code" in c]
                    tokens["code"] = codes
                if "category" in resource_data:
                    categories = []
                    for cat in resource_data["category"]:
                        if "coding" in cat:
                            categories.extend([c["code"] for c in cat["coding"] if "code" in c])
                    tokens["category"] = categories
                    
            # Add more resource types as needed
            
        except Exception as e:
            logger.warning(f"Error extracting search tokens: {e}")
        
        return tokens
