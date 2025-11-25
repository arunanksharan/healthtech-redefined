"""
FHIR Operations Service

Implements FHIR operations including:
- Patient/$everything - Fetch all data related to a patient
- Encounter/$everything - Fetch all data related to an encounter
- $document - Generate a clinical document
- $validate - Validate resources (delegated to ValidationService)
- $meta - Retrieve resource metadata
- $meta-add - Add tags to a resource
- $meta-delete - Remove tags from a resource
"""

from typing import Dict, Any, List, Optional, Set
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from ..repository.fhir_repository import FHIRRepository
from ..validators.validator import FHIRValidator


class OperationsService:
    """
    FHIR Operations Service.

    Provides implementation for FHIR operations including $everything,
    $document, and metadata operations.
    """

    def __init__(self, db: Session):
        """
        Initialize the operations service.

        Args:
            db: Database session
        """
        self.db = db
        self.repository = FHIRRepository(db)
        self.validator = FHIRValidator()

    def patient_everything(
        self,
        tenant_id: UUID,
        patient_id: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        _since: Optional[str] = None,
        _type: Optional[List[str]] = None,
        _count: int = 100
    ) -> Dict[str, Any]:
        """
        Execute Patient/$everything operation.

        Retrieves all clinical data related to a patient including:
        - Patient resource
        - Encounters
        - Observations
        - Conditions
        - Procedures
        - MedicationRequests
        - AllergyIntolerances
        - Related Practitioners and Organizations

        Args:
            tenant_id: Tenant identifier
            patient_id: Patient resource ID
            start: Start date for date-based filtering
            end: End date for date-based filtering
            _since: Only include resources modified since this date
            _type: List of resource types to include (defaults to all)
            _count: Maximum number of resources per type

        Returns:
            FHIR Bundle containing all patient data
        """
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entry": [],
            "total": 0
        }

        seen_ids: Set[str] = set()

        # Default resource types if not specified
        if not _type:
            _type = [
                "Patient", "Encounter", "Observation", "Condition",
                "Procedure", "MedicationRequest", "AllergyIntolerance",
                "Practitioner", "Organization", "Location"
            ]

        # 1. Fetch the Patient resource
        if "Patient" in _type:
            patient = self.repository.get_by_id(
                tenant_id=tenant_id,
                resource_type="Patient",
                resource_id=patient_id
            )

            if not patient:
                raise ValueError(f"Patient/{patient_id} not found")

            bundle["entry"].append({
                "fullUrl": f"Patient/{patient_id}",
                "resource": patient,
                "search": {"mode": "match"}
            })
            seen_ids.add(f"Patient/{patient_id}")

        # Patient reference for searching
        patient_ref = f"Patient/{patient_id}"

        # 2. Fetch Encounters
        if "Encounter" in _type:
            encounters = self._search_by_patient(
                tenant_id, "Encounter", patient_ref,
                start, end, _since, _count
            )
            for encounter in encounters:
                key = f"Encounter/{encounter.get('id')}"
                if key not in seen_ids:
                    bundle["entry"].append({
                        "fullUrl": key,
                        "resource": encounter,
                        "search": {"mode": "match"}
                    })
                    seen_ids.add(key)

        # 3. Fetch Observations
        if "Observation" in _type:
            observations = self._search_by_patient(
                tenant_id, "Observation", patient_ref,
                start, end, _since, _count
            )
            for obs in observations:
                key = f"Observation/{obs.get('id')}"
                if key not in seen_ids:
                    bundle["entry"].append({
                        "fullUrl": key,
                        "resource": obs,
                        "search": {"mode": "match"}
                    })
                    seen_ids.add(key)

        # 4. Fetch Conditions
        if "Condition" in _type:
            conditions = self._search_by_patient(
                tenant_id, "Condition", patient_ref,
                start, end, _since, _count
            )
            for condition in conditions:
                key = f"Condition/{condition.get('id')}"
                if key not in seen_ids:
                    bundle["entry"].append({
                        "fullUrl": key,
                        "resource": condition,
                        "search": {"mode": "match"}
                    })
                    seen_ids.add(key)

        # 5. Fetch Procedures
        if "Procedure" in _type:
            procedures = self._search_by_patient(
                tenant_id, "Procedure", patient_ref,
                start, end, _since, _count
            )
            for proc in procedures:
                key = f"Procedure/{proc.get('id')}"
                if key not in seen_ids:
                    bundle["entry"].append({
                        "fullUrl": key,
                        "resource": proc,
                        "search": {"mode": "match"}
                    })
                    seen_ids.add(key)

        # 6. Fetch MedicationRequests
        if "MedicationRequest" in _type:
            med_requests = self._search_by_patient(
                tenant_id, "MedicationRequest", patient_ref,
                start, end, _since, _count
            )
            for med in med_requests:
                key = f"MedicationRequest/{med.get('id')}"
                if key not in seen_ids:
                    bundle["entry"].append({
                        "fullUrl": key,
                        "resource": med,
                        "search": {"mode": "match"}
                    })
                    seen_ids.add(key)

        # 7. Fetch AllergyIntolerances
        if "AllergyIntolerance" in _type:
            allergies = self._search_by_patient(
                tenant_id, "AllergyIntolerance", patient_ref,
                start, end, _since, _count
            )
            for allergy in allergies:
                key = f"AllergyIntolerance/{allergy.get('id')}"
                if key not in seen_ids:
                    bundle["entry"].append({
                        "fullUrl": key,
                        "resource": allergy,
                        "search": {"mode": "match"}
                    })
                    seen_ids.add(key)

        # 8. Resolve referenced Practitioners and Organizations
        if "Practitioner" in _type or "Organization" in _type:
            for entry in bundle["entry"]:
                resource = entry.get("resource", {})

                # Extract practitioner references
                if "Practitioner" in _type:
                    practitioner_refs = self._extract_references(
                        resource, ["performer", "participant", "requester"]
                    )
                    for ref in practitioner_refs:
                        if ref.startswith("Practitioner/") and ref not in seen_ids:
                            prac_id = ref.replace("Practitioner/", "")
                            practitioner = self.repository.get_by_id(
                                tenant_id=tenant_id,
                                resource_type="Practitioner",
                                resource_id=prac_id
                            )
                            if practitioner:
                                bundle["entry"].append({
                                    "fullUrl": ref,
                                    "resource": practitioner,
                                    "search": {"mode": "include"}
                                })
                                seen_ids.add(ref)

                # Extract organization references
                if "Organization" in _type:
                    org_refs = self._extract_references(
                        resource, ["serviceProvider", "managingOrganization"]
                    )
                    for ref in org_refs:
                        if ref.startswith("Organization/") and ref not in seen_ids:
                            org_id = ref.replace("Organization/", "")
                            organization = self.repository.get_by_id(
                                tenant_id=tenant_id,
                                resource_type="Organization",
                                resource_id=org_id
                            )
                            if organization:
                                bundle["entry"].append({
                                    "fullUrl": ref,
                                    "resource": organization,
                                    "search": {"mode": "include"}
                                })
                                seen_ids.add(ref)

        bundle["total"] = len(bundle["entry"])

        logger.info(
            f"Patient/$everything for {patient_id}: {bundle['total']} resources"
        )

        return bundle

    def encounter_everything(
        self,
        tenant_id: UUID,
        encounter_id: str,
        _type: Optional[List[str]] = None,
        _count: int = 100
    ) -> Dict[str, Any]:
        """
        Execute Encounter/$everything operation.

        Retrieves all clinical data related to an encounter including:
        - Encounter resource
        - Patient
        - Observations within the encounter
        - Conditions diagnosed during the encounter
        - Procedures performed during the encounter
        - Medications prescribed during the encounter
        - Practitioners involved in the encounter
        - Location

        Args:
            tenant_id: Tenant identifier
            encounter_id: Encounter resource ID
            _type: List of resource types to include (defaults to all)
            _count: Maximum number of resources per type

        Returns:
            FHIR Bundle containing all encounter data
        """
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entry": [],
            "total": 0
        }

        seen_ids: Set[str] = set()

        # Default resource types if not specified
        if not _type:
            _type = [
                "Encounter", "Patient", "Observation", "Condition",
                "Procedure", "MedicationRequest", "Practitioner",
                "Organization", "Location"
            ]

        # 1. Fetch the Encounter resource
        encounter = self.repository.get_by_id(
            tenant_id=tenant_id,
            resource_type="Encounter",
            resource_id=encounter_id
        )

        if not encounter:
            raise ValueError(f"Encounter/{encounter_id} not found")

        if "Encounter" in _type:
            bundle["entry"].append({
                "fullUrl": f"Encounter/{encounter_id}",
                "resource": encounter,
                "search": {"mode": "match"}
            })
            seen_ids.add(f"Encounter/{encounter_id}")

        encounter_ref = f"Encounter/{encounter_id}"

        # 2. Fetch the Patient
        if "Patient" in _type:
            subject_ref = encounter.get("subject", {}).get("reference", "")
            if subject_ref and subject_ref not in seen_ids:
                patient_id = subject_ref.replace("Patient/", "")
                patient = self.repository.get_by_id(
                    tenant_id=tenant_id,
                    resource_type="Patient",
                    resource_id=patient_id
                )
                if patient:
                    bundle["entry"].append({
                        "fullUrl": subject_ref,
                        "resource": patient,
                        "search": {"mode": "include"}
                    })
                    seen_ids.add(subject_ref)

        # 3. Fetch Observations linked to encounter
        if "Observation" in _type:
            observations = self._search_by_encounter(
                tenant_id, "Observation", encounter_ref, _count
            )
            for obs in observations:
                key = f"Observation/{obs.get('id')}"
                if key not in seen_ids:
                    bundle["entry"].append({
                        "fullUrl": key,
                        "resource": obs,
                        "search": {"mode": "match"}
                    })
                    seen_ids.add(key)

        # 4. Fetch Conditions linked to encounter
        if "Condition" in _type:
            conditions = self._search_by_encounter(
                tenant_id, "Condition", encounter_ref, _count
            )
            for condition in conditions:
                key = f"Condition/{condition.get('id')}"
                if key not in seen_ids:
                    bundle["entry"].append({
                        "fullUrl": key,
                        "resource": condition,
                        "search": {"mode": "match"}
                    })
                    seen_ids.add(key)

        # 5. Fetch Procedures linked to encounter
        if "Procedure" in _type:
            procedures = self._search_by_encounter(
                tenant_id, "Procedure", encounter_ref, _count
            )
            for proc in procedures:
                key = f"Procedure/{proc.get('id')}"
                if key not in seen_ids:
                    bundle["entry"].append({
                        "fullUrl": key,
                        "resource": proc,
                        "search": {"mode": "match"}
                    })
                    seen_ids.add(key)

        # 6. Fetch MedicationRequests linked to encounter
        if "MedicationRequest" in _type:
            med_requests = self._search_by_encounter(
                tenant_id, "MedicationRequest", encounter_ref, _count
            )
            for med in med_requests:
                key = f"MedicationRequest/{med.get('id')}"
                if key not in seen_ids:
                    bundle["entry"].append({
                        "fullUrl": key,
                        "resource": med,
                        "search": {"mode": "match"}
                    })
                    seen_ids.add(key)

        # 7. Resolve Practitioners from encounter participants
        if "Practitioner" in _type:
            participants = encounter.get("participant", [])
            for participant in participants:
                individual_ref = participant.get("individual", {}).get("reference", "")
                if individual_ref.startswith("Practitioner/") and individual_ref not in seen_ids:
                    prac_id = individual_ref.replace("Practitioner/", "")
                    practitioner = self.repository.get_by_id(
                        tenant_id=tenant_id,
                        resource_type="Practitioner",
                        resource_id=prac_id
                    )
                    if practitioner:
                        bundle["entry"].append({
                            "fullUrl": individual_ref,
                            "resource": practitioner,
                            "search": {"mode": "include"}
                        })
                        seen_ids.add(individual_ref)

        # 8. Resolve Location
        if "Location" in _type:
            locations = encounter.get("location", [])
            for loc in locations:
                loc_ref = loc.get("location", {}).get("reference", "")
                if loc_ref.startswith("Location/") and loc_ref not in seen_ids:
                    loc_id = loc_ref.replace("Location/", "")
                    location = self.repository.get_by_id(
                        tenant_id=tenant_id,
                        resource_type="Location",
                        resource_id=loc_id
                    )
                    if location:
                        bundle["entry"].append({
                            "fullUrl": loc_ref,
                            "resource": location,
                            "search": {"mode": "include"}
                        })
                        seen_ids.add(loc_ref)

        # 9. Resolve Service Provider Organization
        if "Organization" in _type:
            sp_ref = encounter.get("serviceProvider", {}).get("reference", "")
            if sp_ref.startswith("Organization/") and sp_ref not in seen_ids:
                org_id = sp_ref.replace("Organization/", "")
                organization = self.repository.get_by_id(
                    tenant_id=tenant_id,
                    resource_type="Organization",
                    resource_id=org_id
                )
                if organization:
                    bundle["entry"].append({
                        "fullUrl": sp_ref,
                        "resource": organization,
                        "search": {"mode": "include"}
                    })
                    seen_ids.add(sp_ref)

        bundle["total"] = len(bundle["entry"])

        logger.info(
            f"Encounter/$everything for {encounter_id}: {bundle['total']} resources"
        )

        return bundle

    def generate_document(
        self,
        tenant_id: UUID,
        composition_id: str,
        persist: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a clinical document ($document operation).

        Creates a complete FHIR document from a Composition resource,
        resolving all references and bundling them together.

        Args:
            tenant_id: Tenant identifier
            composition_id: Composition resource ID
            persist: Whether to persist the generated document

        Returns:
            FHIR document Bundle
        """
        # Fetch the Composition
        composition = self.repository.get_by_id(
            tenant_id=tenant_id,
            resource_type="Composition",
            resource_id=composition_id
        )

        if not composition:
            raise ValueError(f"Composition/{composition_id} not found")

        bundle = {
            "resourceType": "Bundle",
            "type": "document",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "identifier": {
                "system": "urn:ietf:rfc:3986",
                "value": f"urn:uuid:{composition_id}"
            },
            "entry": []
        }

        seen_ids: Set[str] = set()

        # Composition must be first
        bundle["entry"].append({
            "fullUrl": f"Composition/{composition_id}",
            "resource": composition
        })
        seen_ids.add(f"Composition/{composition_id}")

        # Resolve subject
        subject_ref = composition.get("subject", {}).get("reference", "")
        if subject_ref and subject_ref not in seen_ids:
            self._add_referenced_resource(
                tenant_id, bundle, seen_ids, subject_ref
            )

        # Resolve author(s)
        for author in composition.get("author", []):
            author_ref = author.get("reference", "")
            if author_ref and author_ref not in seen_ids:
                self._add_referenced_resource(
                    tenant_id, bundle, seen_ids, author_ref
                )

        # Resolve custodian
        custodian_ref = composition.get("custodian", {}).get("reference", "")
        if custodian_ref and custodian_ref not in seen_ids:
            self._add_referenced_resource(
                tenant_id, bundle, seen_ids, custodian_ref
            )

        # Resolve section entries
        for section in composition.get("section", []):
            for entry in section.get("entry", []):
                entry_ref = entry.get("reference", "")
                if entry_ref and entry_ref not in seen_ids:
                    self._add_referenced_resource(
                        tenant_id, bundle, seen_ids, entry_ref
                    )

        logger.info(
            f"$document for Composition/{composition_id}: "
            f"{len(bundle['entry'])} resources"
        )

        return bundle

    def get_meta(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str
    ) -> Dict[str, Any]:
        """
        Get resource metadata ($meta operation).

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            resource_id: Resource ID

        Returns:
            Parameters resource with meta information
        """
        resource = self.repository.get_by_id(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id
        )

        if not resource:
            raise ValueError(f"{resource_type}/{resource_id} not found")

        meta = resource.get("meta", {})

        return {
            "resourceType": "Parameters",
            "parameter": [
                {
                    "name": "return",
                    "valueMeta": meta
                }
            ]
        }

    def add_meta(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        tags: Optional[List[Dict[str, str]]] = None,
        security: Optional[List[Dict[str, str]]] = None,
        profiles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add metadata to a resource ($meta-add operation).

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            resource_id: Resource ID
            tags: Tags to add
            security: Security labels to add
            profiles: Profile URLs to add

        Returns:
            Updated meta
        """
        resource = self.repository.get_by_id(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id
        )

        if not resource:
            raise ValueError(f"{resource_type}/{resource_id} not found")

        meta = resource.get("meta", {})

        # Add tags
        if tags:
            existing_tags = meta.get("tag", [])
            for tag in tags:
                if tag not in existing_tags:
                    existing_tags.append(tag)
            meta["tag"] = existing_tags

        # Add security labels
        if security:
            existing_security = meta.get("security", [])
            for sec in security:
                if sec not in existing_security:
                    existing_security.append(sec)
            meta["security"] = existing_security

        # Add profiles
        if profiles:
            existing_profiles = meta.get("profile", [])
            for profile in profiles:
                if profile not in existing_profiles:
                    existing_profiles.append(profile)
            meta["profile"] = existing_profiles

        # Update resource
        resource["meta"] = meta
        self.repository.update(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_data=resource
        )

        return {
            "resourceType": "Parameters",
            "parameter": [
                {
                    "name": "return",
                    "valueMeta": meta
                }
            ]
        }

    def delete_meta(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        tags: Optional[List[Dict[str, str]]] = None,
        security: Optional[List[Dict[str, str]]] = None,
        profiles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Remove metadata from a resource ($meta-delete operation).

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            resource_id: Resource ID
            tags: Tags to remove
            security: Security labels to remove
            profiles: Profile URLs to remove

        Returns:
            Updated meta
        """
        resource = self.repository.get_by_id(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id
        )

        if not resource:
            raise ValueError(f"{resource_type}/{resource_id} not found")

        meta = resource.get("meta", {})

        # Remove tags
        if tags:
            existing_tags = meta.get("tag", [])
            meta["tag"] = [t for t in existing_tags if t not in tags]

        # Remove security labels
        if security:
            existing_security = meta.get("security", [])
            meta["security"] = [s for s in existing_security if s not in security]

        # Remove profiles
        if profiles:
            existing_profiles = meta.get("profile", [])
            meta["profile"] = [p for p in existing_profiles if p not in profiles]

        # Update resource
        resource["meta"] = meta
        self.repository.update(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_data=resource
        )

        return {
            "resourceType": "Parameters",
            "parameter": [
                {
                    "name": "return",
                    "valueMeta": meta
                }
            ]
        }

    def _search_by_patient(
        self,
        tenant_id: UUID,
        resource_type: str,
        patient_ref: str,
        start: Optional[str],
        end: Optional[str],
        since: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search for resources by patient reference."""
        search_params = {"subject": patient_ref}

        # Add date filters if provided
        if start:
            search_params["date"] = f"ge{start}"
        if end:
            if "date" in search_params:
                # Would need to handle multiple date params
                pass
            else:
                search_params["date"] = f"le{end}"

        bundle = self.repository.search(
            tenant_id=tenant_id,
            resource_type=resource_type,
            search_params=search_params,
            limit=limit,
            offset=0
        )

        return [entry.get("resource") for entry in bundle.get("entry", [])]

    def _search_by_encounter(
        self,
        tenant_id: UUID,
        resource_type: str,
        encounter_ref: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search for resources by encounter reference."""
        bundle = self.repository.search(
            tenant_id=tenant_id,
            resource_type=resource_type,
            search_params={"encounter": encounter_ref},
            limit=limit,
            offset=0
        )

        return [entry.get("resource") for entry in bundle.get("entry", [])]

    def _extract_references(
        self,
        resource: Dict[str, Any],
        fields: List[str]
    ) -> List[str]:
        """Extract reference values from specified fields."""
        references = []

        for field in fields:
            value = resource.get(field)
            if not value:
                continue

            if isinstance(value, dict):
                if "reference" in value:
                    references.append(value["reference"])
                elif "individual" in value and "reference" in value["individual"]:
                    references.append(value["individual"]["reference"])
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        if "reference" in item:
                            references.append(item["reference"])
                        elif "individual" in item:
                            individual = item.get("individual", {})
                            if "reference" in individual:
                                references.append(individual["reference"])

        return references

    def _add_referenced_resource(
        self,
        tenant_id: UUID,
        bundle: Dict[str, Any],
        seen_ids: Set[str],
        reference: str
    ):
        """Fetch and add a referenced resource to the bundle."""
        if "/" not in reference:
            return

        parts = reference.split("/")
        resource_type = parts[-2]
        resource_id = parts[-1]

        resource = self.repository.get_by_id(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id
        )

        if resource:
            bundle["entry"].append({
                "fullUrl": reference,
                "resource": resource
            })
            seen_ids.add(reference)
