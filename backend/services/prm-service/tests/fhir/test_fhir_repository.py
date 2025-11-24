"""
Test FHIR Repository
Unit tests for FHIR resource CRUD operations
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from shared.database.fhir_models import Base, FHIRResource, FHIRResourceHistory
from services.prm-service.modules.fhir.repository.fhir_repository import FHIRRepository


# Test database setup
@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def repository(db_session):
    """Create a repository instance"""
    return FHIRRepository(db_session)


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_patient():
    """Sample Patient resource"""
    return {
        "resourceType": "Patient",
        "identifier": [
            {
                "system": "http://hospital.example.org/mrn",
                "value": "MRN12345"
            }
        ],
        "name": [
            {
                "family": "Smith",
                "given": ["John", "David"]
            }
        ],
        "gender": "male",
        "birthDate": "1990-01-01"
    }


# ============================================================================
# CREATE TESTS
# ============================================================================

def test_create_patient(repository, tenant_id, sample_patient):
    """Test creating a Patient resource"""
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient
    )

    assert created is not None
    assert created["id"] is not None
    assert created["resourceType"] == "Patient"
    assert created["meta"]["versionId"] == "1"
    assert "lastUpdated" in created["meta"]


def test_create_with_custom_id(repository, tenant_id, sample_patient):
    """Test creating a resource with a custom ID"""
    custom_id = "patient-123"
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient,
        resource_id=custom_id
    )

    assert created["id"] == custom_id


def test_create_with_search_tokens(repository, tenant_id, sample_patient):
    """Test that search tokens are extracted on create"""
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient
    )

    # Verify resource was created
    assert created["id"] is not None

    # Retrieve from database to check tokens
    db_resource = repository.db.query(FHIRResource).filter(
        FHIRResource.fhir_id == created["id"]
    ).first()

    assert db_resource is not None
    assert db_resource.search_tokens is not None
    assert "identifier" in db_resource.search_tokens
    assert "MRN12345" in db_resource.search_tokens["identifier"]


# ============================================================================
# READ TESTS
# ============================================================================

def test_get_by_id(repository, tenant_id, sample_patient):
    """Test retrieving a resource by ID"""
    # Create a resource
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient
    )

    # Retrieve it
    retrieved = repository.get_by_id(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id=created["id"]
    )

    assert retrieved is not None
    assert retrieved["id"] == created["id"]
    assert retrieved["resourceType"] == "Patient"


def test_get_nonexistent_resource(repository, tenant_id):
    """Test retrieving a nonexistent resource"""
    retrieved = repository.get_by_id(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id="nonexistent-id"
    )

    assert retrieved is None


def test_get_deleted_resource(repository, tenant_id, sample_patient):
    """Test that deleted resources are not returned"""
    # Create and delete a resource
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient
    )

    repository.delete(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id=created["id"]
    )

    # Try to retrieve it
    retrieved = repository.get_by_id(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id=created["id"]
    )

    assert retrieved is None


# ============================================================================
# UPDATE TESTS
# ============================================================================

def test_update_resource(repository, tenant_id, sample_patient):
    """Test updating a resource"""
    # Create a resource
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient
    )

    # Update it
    updated_data = created.copy()
    updated_data["gender"] = "female"

    updated = repository.update(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id=created["id"],
        resource_data=updated_data
    )

    assert updated["id"] == created["id"]
    assert updated["gender"] == "female"
    assert updated["meta"]["versionId"] == "2"


def test_update_increments_version(repository, tenant_id, sample_patient):
    """Test that updates increment the version"""
    # Create a resource
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient
    )

    # Update multiple times
    for i in range(3):
        updated_data = created.copy()
        updated_data["name"][0]["family"] = f"Smith-{i}"

        updated = repository.update(
            tenant_id=tenant_id,
            resource_type="Patient",
            resource_id=created["id"],
            resource_data=updated_data
        )

        assert updated["meta"]["versionId"] == str(i + 2)


# ============================================================================
# DELETE TESTS
# ============================================================================

def test_delete_resource(repository, tenant_id, sample_patient):
    """Test deleting a resource"""
    # Create a resource
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient
    )

    # Delete it
    deleted = repository.delete(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id=created["id"]
    )

    assert deleted is True

    # Verify it's not returned
    retrieved = repository.get_by_id(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id=created["id"]
    )

    assert retrieved is None


def test_delete_nonexistent_resource(repository, tenant_id):
    """Test deleting a nonexistent resource"""
    deleted = repository.delete(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id="nonexistent-id"
    )

    assert deleted is False


# ============================================================================
# SEARCH TESTS
# ============================================================================

def test_search_all_resources(repository, tenant_id, sample_patient):
    """Test searching for all resources of a type"""
    # Create multiple patients
    for i in range(3):
        patient = sample_patient.copy()
        patient["name"][0]["family"] = f"Smith-{i}"
        repository.create(
            tenant_id=tenant_id,
            resource_type="Patient",
            resource_data=patient
        )

    # Search
    bundle = repository.search(
        tenant_id=tenant_id,
        resource_type="Patient",
        search_params={}
    )

    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "searchset"
    assert bundle["total"] >= 3
    assert len(bundle["entry"]) >= 3


def test_search_with_pagination(repository, tenant_id, sample_patient):
    """Test search with pagination"""
    # Create multiple patients
    for i in range(10):
        patient = sample_patient.copy()
        patient["name"][0]["family"] = f"Smith-{i}"
        repository.create(
            tenant_id=tenant_id,
            resource_type="Patient",
            resource_data=patient
        )

    # Search with pagination
    bundle = repository.search(
        tenant_id=tenant_id,
        resource_type="Patient",
        search_params={},
        limit=5,
        offset=0
    )

    assert len(bundle["entry"]) == 5


def test_search_by_id(repository, tenant_id, sample_patient):
    """Test searching by resource ID"""
    # Create a resource
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient
    )

    # Search by ID
    bundle = repository.search(
        tenant_id=tenant_id,
        resource_type="Patient",
        search_params={"_id": created["id"]}
    )

    assert bundle["total"] == 1
    assert bundle["entry"][0]["resource"]["id"] == created["id"]


# ============================================================================
# HISTORY TESTS
# ============================================================================

def test_get_history(repository, tenant_id, sample_patient):
    """Test retrieving resource history"""
    # Create a resource
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient
    )

    # Update it multiple times
    for i in range(3):
        updated_data = created.copy()
        updated_data["name"][0]["family"] = f"Smith-{i}"

        repository.update(
            tenant_id=tenant_id,
            resource_type="Patient",
            resource_id=created["id"],
            resource_data=updated_data
        )

    # Get history
    versions = repository.get_history(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id=created["id"]
    )

    # Should have 4 versions (1 create + 3 updates)
    assert len(versions) == 4

    # Versions should be in descending order
    version_ids = [v["meta"]["versionId"] for v in versions]
    assert version_ids == ["4", "3", "2", "1"]


def test_history_includes_deletes(repository, tenant_id, sample_patient):
    """Test that history includes delete operations"""
    # Create and delete a resource
    created = repository.create(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_data=sample_patient
    )

    repository.delete(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id=created["id"]
    )

    # Get history
    versions = repository.get_history(
        tenant_id=tenant_id,
        resource_type="Patient",
        resource_id=created["id"]
    )

    # Should have 2 versions (create + delete)
    assert len(versions) == 2


# ============================================================================
# MULTI-TENANCY TESTS
# ============================================================================

def test_tenant_isolation(repository, sample_patient):
    """Test that resources are isolated by tenant"""
    tenant1 = UUID("00000000-0000-0000-0000-000000000001")
    tenant2 = UUID("00000000-0000-0000-0000-000000000002")

    # Create resource for tenant1
    created = repository.create(
        tenant_id=tenant1,
        resource_type="Patient",
        resource_data=sample_patient
    )

    # Try to retrieve it as tenant2
    retrieved = repository.get_by_id(
        tenant_id=tenant2,
        resource_type="Patient",
        resource_id=created["id"]
    )

    assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
